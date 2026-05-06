"""
Database models and initialization for Shadow Supply Chain system v4.0 (ShadowSync AI).
Uses SQLAlchemy ORM with SQLite in WAL mode for concurrency safety (LP-C1).

New in v4.0:
  - WAL mode + busy_timeout pragma (LP-C1)
  - reviewer_verdict on ShadowPurchase (LP-01)
  - DetectionThreshold, ConfidenceDecayLog, VerificationTask (LP-02)
  - SignalEvent for multi-signal ingestion (LP-03)
  - PartsCompatibility, MachineCriticality (LP-04)
  - ShiftRoster, WarehouseAccess (LP-06)
  - InventoryLocation, WarehouseTransferCost (LP-12)
  - DepletionAlert, MachineUsageLog (LP-11)
  - UserTrustMetric (LP-08)
  - ItemSynonym (LP-09)
  - RiskScoreHistory (LP-10)
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime, os, csv, random

Base = declarative_base()
DB_PATH = os.path.join(os.path.dirname(__file__), "shadow_supply.db")
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_size=10,
    max_overflow=20
)

# ─── LP-C1: SQLite WAL Mode for concurrency safety ────────────
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String)
    risk_level = Column(String, default="Medium")  # Low, Medium, High
    approved = Column(Boolean, default=False)
    avg_order = Column(Float, default=0)
    trust_score = Column(Float, default=50.0)  # 0-100 trust score


class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, unique=True)
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
    category = Column(String)
    reorder_level = Column(Integer, default=0)
    location = Column(String)
    last_updated = Column(String, nullable=True)  # ISO datetime string for tracking


class Procurement(Base):
    __tablename__ = "procurement"
    id = Column(String, primary_key=True)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    vendor_name = Column(String)
    item = Column(String)
    amount = Column(Float)
    quantity = Column(Integer, default=1)
    date = Column(String)
    status = Column(String, default="Pending")  # Pending, Approved, Delivered, Resolved
    department = Column(String)
    source = Column(String, default="Manual")  # Manual | Shadow-Resolved


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(String, primary_key=True)
    date = Column(String)
    vendor = Column(String)
    amount = Column(Float)
    description = Column(String)
    payment_type = Column(String)  # Invoice, Corporate Card, Expense Claim
    card_holder = Column(String)
    department = Column(String)
    is_shadow = Column(Boolean, default=False)
    matched_po_id = Column(String, nullable=True)
    ai_risk_score = Column(Float, default=0.0)
    ai_category = Column(String, nullable=True)

    # Relationship to shadow purchase
    shadow_purchase = relationship("ShadowPurchase", back_populates="transaction", uselist=False)


class ShadowPurchase(Base):
    __tablename__ = "shadow_purchases"

    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    detected_at = Column(String)
    reason = Column(String)
    risk_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=1.0)      # System confidence in prediction
    data_quality_flag = Column(String, default="Good") # Good, Vague, Missing Data
    status = Column(String, default="Pending")         # Pending, Resolved, Ignored, Auto-Resolved
    resolved_po_id = Column(String, nullable=True)
    item_category = Column(String, nullable=True)

    # Priority Queue Engine fields
    priority_score = Column(Float, default=0.0)
    estimated_loss = Column(Float, default=0.0)
    frequency = Column(Integer, default=1)

    # LP-01: Feedback loop fields
    reviewer_verdict = Column(String, nullable=True)   # confirmed_shadow | false_positive | needs_review
    reviewed_at = Column(String, nullable=True)
    reviewer_id = Column(String, nullable=True)

    # Relationships
    transaction = relationship("Transaction", back_populates="shadow_purchase")
    action_recommendations = relationship("ActionRecommendation", back_populates="shadow_purchase")
    behavior_metrics = relationship("BehaviorMetric", back_populates="shadow_purchase")
    user_feedback = relationship("UserFeedback", back_populates="shadow_purchase")
    audit_log = relationship("AuditLog", back_populates="shadow_purchase")
    risk_history = relationship("RiskScoreHistory", back_populates="shadow_purchase")


class RiskSnapshot(Base):
    """Aggregate real-time risk snapshots — stored after each detection cycle."""
    __tablename__ = "risk_snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    total_exposure = Column(Float, default=0.0)
    shadow_rate = Column(Float, default=0.0)
    avg_risk_score = Column(Float, default=0.0)
    high_risk_count = Column(Integer, default=0)
    risk_level = Column(String, default="Low")
    pending_actions = Column(Integer, default=0)


class RiskMetric(Base):
    """Individual financial impact analysis for a specific shadow purchase."""
    __tablename__ = "risk_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey("transactions.id"))
    risk_score = Column(Float, default=0.0)
    estimated_loss = Column(Float, default=0.0)
    category = Column(String, default="Low")           # Low, Medium, High


class ActionRecommendation(Base):
    """Decisions and next steps for shadow purchases."""
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=True)
    transaction_id = Column(String, ForeignKey("transactions.id"))
    recommendation_text = Column(String, nullable=False)
    priority = Column(String, default="Medium")        # Low, Medium, High, Critical
    action_taken = Column(String, nullable=True)       # What action was taken
    created_at = Column(String, nullable=True)         # ISO timestamp when created

    # Relationship
    shadow_purchase = relationship("ShadowPurchase", back_populates="action_recommendations")


class BehaviorMetric(Base):
    """Pattern tracking for accountability and operational analysis."""
    __tablename__ = "behavior_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=True)
    employee_id = Column(String)                       # Card holder name in this context
    department = Column(String)
    shadow_count = Column(Integer, default=0)
    risk_level = Column(String, default="Low")

    # Relationship
    shadow_purchase = relationship("ShadowPurchase", back_populates="behavior_metrics")


class UserFeedback(Base):
    """Human-in-the-loop corrections on AI predictions."""
    __tablename__ = "user_feedback"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=True)
    transaction_id = Column(String, nullable=True)
    feedback_type = Column(String, nullable=False)     # correct, incorrect, recategorize
    original_category = Column(String, nullable=True)
    corrected_category = Column(String, nullable=True)
    original_risk = Column(Float, nullable=True)
    corrected_risk = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    submitted_at = Column(String, nullable=False)
    applied = Column(Boolean, default=False)           # Whether feedback was applied to model

    # Relationship
    shadow_purchase = relationship("ShadowPurchase", back_populates="user_feedback")


class AuditLog(Base):
    """Compliance and accountability tracking for all human and system actions."""
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=True)
    timestamp = Column(String, nullable=False)         # ISO format
    action = Column(String, nullable=False)            # RECTIFY, DISMISS, FEEDBACK, MODE_CHANGE

    user = Column(String, default="System Administrator")
    target_id = Column(String, nullable=True)          # Shadow ID, PO ID, or Transaction ID
    details = Column(Text, nullable=True)              # JSON or human-readable description

    # Relationship
    shadow_purchase = relationship("ShadowPurchase", back_populates="audit_log")



class TrendMetric(Base):
    """Track trends over time for analytics."""
    __tablename__ = "trend_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)  # ISO date string
    metric_type = Column(String)  # 'shadow_count', 'vendor_risk', 'department_activity', 'category_distribution'
    value = Column(Float)
    category = Column(String, nullable=True)  # e.g., vendor name or department name
    details = Column(Text, nullable=True)  # JSON string for additional data


class ActionLog(Base):
    """Track actions taken by analysts on shadow purchases."""
    __tablename__ = "action_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=True)
    timestamp = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    user = Column(String, default="System Administrator")
    notes = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)


# ═══════════════════════════════════════════════
# LP-01: Detection Feedback & Retraining
# ═══════════════════════════════════════════════

class DetectionThreshold(Base):
    """Per-vendor/category anomaly detection weights, adjusted by feedback."""
    __tablename__ = "detection_thresholds"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_pattern = Column(String, nullable=False)
    category = Column(String, nullable=True)
    anomaly_weight = Column(Float, default=1.0)   # Multiplier: lower = less sensitive
    false_positive_count = Column(Integer, default=0)
    confirmed_shadow_count = Column(Integer, default=0)
    updated_at = Column(String, nullable=True)


# ═══════════════════════════════════════════════
# LP-02: Confidence Decay & Verification
# ═══════════════════════════════════════════════

class ConfidenceDecayLog(Base):
    """Records every time confidence score decays on an AI-auto-updated record."""
    __tablename__ = "confidence_decay_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    delta = Column(Float, nullable=False)           # How much confidence changed
    reason = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)


class VerificationTask(Base):
    """Tasks created when inventory confidence drops below threshold."""
    __tablename__ = "verification_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    location = Column(String, nullable=True)
    priority = Column(String, default="normal")     # normal | urgent
    reason = Column(String, nullable=True)
    requested_at = Column(String, nullable=False)
    status = Column(String, default="pending")      # pending | confirmed | missed
    verifier_id = Column(String, nullable=True)
    confirmed_quantity = Column(Integer, nullable=True)
    resolved_at = Column(String, nullable=True)


# ═══════════════════════════════════════════════
# LP-03: Multi-Signal Ingestion
# ═══════════════════════════════════════════════

class SignalEvent(Base):
    """Unified multi-signal events: gate entries, petty cash, dept transfers."""
    __tablename__ = "signal_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String, nullable=False)    # gate_entry | petty_cash | dept_transfer
    timestamp = Column(String, nullable=False)
    raw_data = Column(Text, nullable=True)          # JSON string
    correlated_shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=True)
    evidence_strength = Column(Integer, default=1)  # 1=weak, 2=moderate, 3+=strong
    flagged = Column(Boolean, default=False)


# ═══════════════════════════════════════════════
# LP-04: Parts Compatibility & Machine Criticality
# ═══════════════════════════════════════════════

class PartsCompatibility(Base):
    """OEM-validated substitute parts with criticality gate."""
    __tablename__ = "parts_compatibility"
    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_sku = Column(String, nullable=False)
    substitute_sku = Column(String, nullable=False)
    compatibility_score = Column(Integer, default=0)    # 0-100
    validated_by = Column(String, default="unvalidated") # oem | engineer_approved | unvalidated
    safe_for_critical = Column(Boolean, default=False)


class MachineCriticality(Base):
    """Machine criticality levels for safety-gated substitute decisions."""
    __tablename__ = "machine_criticality"
    machine_id = Column(String, primary_key=True)
    criticality_level = Column(String, default="standard")  # critical | high | standard
    downtime_cost_per_hour = Column(Float, default=0.0)


# ═══════════════════════════════════════════════
# LP-06: Workforce-Aware Retrieval ETA
# ═══════════════════════════════════════════════

class ShiftRoster(Base):
    """Warehouse staff shift schedules."""
    __tablename__ = "shift_roster"
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(String, nullable=False)
    warehouse_id = Column(String, nullable=False)
    shift_start = Column(String, nullable=False)   # HH:MM format
    shift_end = Column(String, nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon, 6=Sun
    is_holiday = Column(Boolean, default=False)


class WarehouseAccess(Base):
    """Staff access permissions per warehouse."""
    __tablename__ = "warehouse_access"
    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(String, nullable=False)
    warehouse_id = Column(String, nullable=False)
    access_level = Column(String, default="full")  # full | restricted | none


# ═══════════════════════════════════════════════
# LP-08: User Trust Momentum
# ═══════════════════════════════════════════════

class UserTrustMetric(Base):
    """Per-user trust and cost-savings metrics."""
    __tablename__ = "user_trust_metrics"
    user_id = Column(String, primary_key=True)
    total_checks = Column(Integer, default=0)
    followed_recommendations = Column(Integer, default=0)
    overrides_that_were_correct = Column(Integer, default=0)
    internal_retrievals_successful = Column(Integer, default=0)
    estimated_cost_saved = Column(Float, default=0.0)
    estimated_time_saved_minutes = Column(Integer, default=0)
    trust_score = Column(Float, default=50.0)       # 0-100


# ═══════════════════════════════════════════════
# LP-09: Item Synonym Normalization
# ═══════════════════════════════════════════════

class ItemSynonym(Base):
    """Canonical SKU → raw description synonym mappings."""
    __tablename__ = "item_synonyms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_sku = Column(String, nullable=False)
    synonym = Column(String, nullable=False)
    source = Column(String, default="manual")      # manual | auto_learned


# ═══════════════════════════════════════════════
# LP-10: Living Risk Score History
# ═══════════════════════════════════════════════

class RiskScoreHistory(Base):
    """Event-driven risk score time series per shadow purchase."""
    __tablename__ = "risk_score_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=False)
    score = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)
    trigger_event = Column(String, nullable=True)  # e.g. 'po_retroactively_matched'

    shadow_purchase = relationship("ShadowPurchase", back_populates="risk_history")


# ═══════════════════════════════════════════════
# LP-11: Predictive Depletion
# ═══════════════════════════════════════════════

class MachineUsageLog(Base):
    """Historical part consumption per machine, used for depletion prediction."""
    __tablename__ = "machine_usage_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, nullable=False)
    part_sku = Column(String, nullable=False)
    event_type = Column(String, nullable=False)    # replacement | failure | scheduled_maintenance
    event_date = Column(String, nullable=False)
    quantity_used = Column(Integer, default=1)


class DepletionAlert(Base):
    """Pre-emptive stock-out predictions with suggested order quantities."""
    __tablename__ = "depletion_alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    predicted_need_date = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    suggested_order_qty = Column(Integer, default=0)
    status = Column(String, default="pending")     # pending | ordered | dismissed
    created_at = Column(String, nullable=False)


# ═══════════════════════════════════════════════
# LP-12: Cross-Warehouse Inventory Mesh
# ═══════════════════════════════════════════════

class InventoryLocation(Base):
    """Per-warehouse stock levels with confidence scores."""
    __tablename__ = "inventory_locations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    warehouse_id = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    confidence_score = Column(Float, default=80.0)
    last_verified = Column(String, nullable=True)


class WarehouseTransferCost(Base):
    """Transfer cost and ETA matrix between warehouse pairs."""
    __tablename__ = "warehouse_transfer_costs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_warehouse = Column(String, nullable=False)
    to_warehouse = Column(String, nullable=False)
    distance_km = Column(Float, default=0.0)
    eta_minutes = Column(Integer, default=30)
    cost_per_transfer = Column(Float, default=0.0)


def init_db():
    """Create tables and seed from CSV files."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Add some seed trends if empty
    from database import TrendMetric, RiskSnapshot
    if not db.query(TrendMetric).first():
        today = datetime.date.today()
        for i in range(10):
            d = (today - datetime.timedelta(days=10-i)).isoformat()
            db.add(TrendMetric(date=d, metric_type="shadow_count", value=float(random.randint(5, 20))))
            db.add(TrendMetric(date=d, metric_type="financial_exposure", value=float(random.randint(5000, 15000))))
            db.add(RiskSnapshot(
                timestamp=d + "T12:00:00",
                total_exposure=float(random.randint(5000, 15000)),
                shadow_rate=0.1 + (random.random() * 0.1),
                avg_risk_score=0.3 + (random.random() * 0.4),
                high_risk_count=random.randint(1, 5),
                risk_level="Medium",
                pending_actions=random.randint(5, 10)
            ))
        db.commit()

    # Only seed CSV data if empty
def _migrate_columns(connection):
    """Add new columns to existing tables safely (idempotent)."""
    cursor = connection.cursor()
    migrations = [
        ("ALTER TABLE shadow_purchases ADD COLUMN reviewer_verdict TEXT", "reviewer_verdict"),
        ("ALTER TABLE shadow_purchases ADD COLUMN reviewed_at TEXT", "reviewed_at"),
        ("ALTER TABLE shadow_purchases ADD COLUMN reviewer_id TEXT", "reviewer_id"),
    ]
    for sql, col_name in migrations:
        try:
            cursor.execute(sql)
        except Exception:
            pass  # Column already exists
    connection.commit()


def init_db():
    """Create tables, run migrations, and seed from CSV files."""
    Base.metadata.create_all(bind=engine)

    # Run safe column migrations on the raw connection
    raw_conn = engine.raw_connection()
    _migrate_columns(raw_conn)
    raw_conn.close()

    db = SessionLocal()

    # Seed trend metrics
    from database import TrendMetric, RiskSnapshot
    if not db.query(TrendMetric).first():
        today = datetime.date.today()
        for i in range(10):
            d = (today - datetime.timedelta(days=10-i)).isoformat()
            db.add(TrendMetric(date=d, metric_type="shadow_count", value=float(random.randint(5, 20))))
            db.add(TrendMetric(date=d, metric_type="financial_exposure", value=float(random.randint(5000, 15000))))
            db.add(RiskSnapshot(
                timestamp=d + "T12:00:00",
                total_exposure=float(random.randint(5000, 15000)),
                shadow_rate=0.1 + (random.random() * 0.1),
                avg_risk_score=0.3 + (random.random() * 0.4),
                high_risk_count=random.randint(1, 5),
                risk_level="Medium",
                pending_actions=random.randint(5, 10)
            ))
        db.commit()

    # Seed LP-12: Warehouse Transfer Costs
    if not db.query(WarehouseTransferCost).first():
        pairs = [
            ("Warehouse A", "Warehouse B", 12.0, 18, 50.0),
            ("Warehouse A", "Warehouse C", 45.0, 65, 120.0),
            ("Warehouse B", "Warehouse A", 12.0, 18, 50.0),
            ("Warehouse B", "Warehouse C", 38.0, 55, 95.0),
            ("Warehouse C", "Warehouse A", 45.0, 65, 120.0),
            ("Warehouse C", "Warehouse B", 38.0, 55, 95.0),
        ]
        for f, t, d, e, c in pairs:
            db.add(WarehouseTransferCost(from_warehouse=f, to_warehouse=t, distance_km=d, eta_minutes=e, cost_per_transfer=c))
        db.commit()

    # Seed LP-06: Shift Roster (demo data)
    if not db.query(ShiftRoster).first():
        staff = [("W001", "Warehouse A"), ("W002", "Warehouse A"), ("W003", "Warehouse B"), ("W004", "Warehouse C")]
        for staff_id, wh in staff:
            for dow in range(5):  # Mon–Fri
                db.add(ShiftRoster(staff_id=staff_id, warehouse_id=wh, shift_start="07:00", shift_end="15:00", day_of_week=dow))
                db.add(WarehouseAccess(staff_id=staff_id, warehouse_id=wh, access_level="full"))
        db.commit()

    # Seed LP-04: Machine criticality
    if not db.query(MachineCriticality).first():
        machines = [
            ("MACH-001", "critical", 5000.0),
            ("MACH-002", "high", 2000.0),
            ("MACH-003", "standard", 500.0),
        ]
        for mid, level, cost in machines:
            db.add(MachineCriticality(machine_id=mid, criticality_level=level, downtime_cost_per_hour=cost))
        db.commit()

    # Seed LP-09: Item synonyms
    if not db.query(ItemSynonym).first():
        synonyms = [
            ("HP-XL-001", "hydro pump xl", "manual"),
            ("HP-XL-001", "hydraulic pump extra large", "manual"),
            ("HP-XL-001", "pump xl", "manual"),
            ("SB-M10-40", "steel bolt m10x40", "manual"),
            ("SB-M10-40", "m10 bolt 40mm", "manual"),
            ("SB-M10-40", "bolt m10", "manual"),
        ]
        for sku, syn, src in synonyms:
            db.add(ItemSynonym(canonical_sku=sku, synonym=syn, source=src))
        db.commit()

    # Only seed CSV data if empty
    from database import Vendor
    if db.query(Vendor).first():
        db.close()
        return

    data_dir = os.path.join(os.path.dirname(__file__), "data")

    # Vendors
    with open(os.path.join(data_dir, "vendors.csv")) as f:
        for row in csv.DictReader(f):
            trust = {"Low": 80, "Medium": 50, "High": 20}.get(row["risk_level"], 50)
            db.add(Vendor(id=row["id"], name=row["name"], category=row["category"],
                          risk_level=row["risk_level"], approved=row["approved"] == "True",
                          avg_order=float(row["avg_order"]), trust_score=float(trust)))

    # Inventory + seed InventoryLocation for LP-12
    with open(os.path.join(data_dir, "inventory.csv")) as f:
        for row in csv.DictReader(f):
            db.add(Inventory(id=row["id"], name=row["name"], sku=row["sku"],
                             quantity=int(row["quantity"]), unit_price=float(row["unit_price"]),
                             category=row["category"], reorder_level=int(row["reorder_level"]),
                             location=row["location"]))
            # Mirror into multi-location table
            db.add(InventoryLocation(
                sku=row["sku"],
                warehouse_id=row["location"],
                quantity=int(row["quantity"]),
                confidence_score=80.0,
                last_verified=datetime.datetime.now().isoformat()
            ))

    # Procurement
    with open(os.path.join(data_dir, "procurement_records.csv")) as f:
        for row in csv.DictReader(f):
            db.add(Procurement(id=row["id"], vendor_id=row["vendor_id"], vendor_name=row["vendor_name"],
                               item=row["item"], amount=float(row["amount"]), quantity=int(row["quantity"]),
                               date=row["date"], status=row["status"], department=row["department"]))

    # Transactions
    with open(os.path.join(data_dir, "financial_transactions.csv")) as f:
        for row in csv.DictReader(f):
            db.add(Transaction(id=row["id"], date=row["date"], vendor=row["vendor"],
                               amount=float(row["amount"]), description=row["description"],
                               payment_type=row["payment_type"], card_holder=row["card_holder"],
                               department=row["department"]))

    db.commit()
    db.close()
    print("[OK] Database initialized and seeded.")


if __name__ == "__main__":
    init_db()

