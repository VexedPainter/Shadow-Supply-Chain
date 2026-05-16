"""
Database models and initialization for Shadow Supply Chain system v3.0.
Uses SQLAlchemy ORM with SQLite.
Includes: RiskSnapshot, RiskMetric, ActionRecommendation, BehaviorMetric, and UserFeedback.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime, os, csv, random
import uuid as _uuid

Base = declarative_base()

# ─── B5: Dynamic Database URL (SQLite for dev, PostgreSQL for production) ───
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(os.path.dirname(__file__), 'shadow_supply.db')}"  # fallback for local dev
)

# Handle PostgreSQL URL format from cloud providers (Render, Railway, Heroku)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "sqlite" in DATABASE_URL:
    # SQLite-specific path extraction
    DB_PATH = DATABASE_URL.replace("sqlite:///", "")
    connect_args = {"check_same_thread": False, "timeout": 30}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_size=10,
        max_overflow=20
    )
else:
    # PostgreSQL — no check_same_thread, use connection pooling
    connect_args = {}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Only apply SQLite PRAGMAs for SQLite connections
    if "sqlite" in DATABASE_URL:
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
    # F5: Supplier network graph fields
    tier = Column(Integer, default=1)                   # 1=direct, 2=sub-supplier, 3=raw material
    alternative_vendors = Column(String, default="")    # comma-separated backup vendor names
    # F11: ESG compliance fields
    esg_score = Column(Float, default=50.0)             # 0-100 sustainability score
    carbon_rating = Column(String, default="C")         # A/B/C/D/F
    sustainability_certified = Column(Boolean, default=False)
    portal_token = Column(String, unique=True, default=lambda: str(_uuid.uuid4()))


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
    vendor = Column(String, index=True)        # indexed: PO matching scans by vendor
    amount = Column(Float)
    description = Column(String)
    payment_type = Column(String)  # Invoice, Corporate Card, Expense Claim
    card_holder = Column(String)
    department = Column(String, index=True)    # indexed: department-level risk queries
    is_shadow = Column(Boolean, default=False, index=True)  # indexed: shadow filter is hot path
    matched_po_id = Column(String, nullable=True)
    ai_risk_score = Column(Float, default=0.0)
    ai_category = Column(String, nullable=True)
    # B7: Multi-currency support
    currency = Column(String, default="USD")           # Original transaction currency
    amount_usd = Column(Float, nullable=True)          # Normalized to USD for ML scoring
    exchange_rate = Column(Float, default=1.0)         # Rate applied at time of transaction

    # Relationship to shadow purchase
    shadow_purchase = relationship("ShadowPurchase", back_populates="transaction", uselist=False)


class ShadowPurchase(Base):
    __tablename__ = "shadow_purchases"

    # Core fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True, index=True)
    detected_at = Column(String)
    reason = Column(String)
    risk_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=1.0)      # System confidence in prediction
    data_quality_flag = Column(String, default="Good") # Good, Vague, Missing Data
    status = Column(String, default="Pending", index=True)         # Pending, Resolved, Ignored
    resolved_po_id = Column(String, nullable=True)
    item_category = Column(String, nullable=True)

    # Priority Queue Engine fields - NEW
    priority_score = Column(Float, default=0.0)        # Calculated priority score
    estimated_loss = Column(Float, default=0.0)       # Financial impact estimate
    frequency = Column(Integer, default=1)            # Pattern frequency count

    # Detection Layer & Bypass Link
    confirmed_shadow = Column(Boolean, default=False)
    false_positive = Column(Boolean, default=False)
    needs_review = Column(Boolean, default=True, index=True)   # indexed: recalibration job filter
    bypassed_preventive = Column(Boolean, default=False)
    
    # Phase 3 - LP-01 Feedback fields
    reviewer_verdict = Column(String, nullable=True) # 'confirmed_shadow', 'false_positive', 'needs_review'
    reviewed_at = Column(String, nullable=True)
    reviewer_id = Column(String, nullable=True)

    # LP-01 idempotency guard: set True once recalibration_job has applied this verdict to vendor trust.
    # Persisted in DB so server restarts never cause double-application of feedback adjustments.
    recalibration_applied = Column(Boolean, default=False, nullable=False)

    # Relationships
    transaction = relationship("Transaction", back_populates="shadow_purchase")
    action_recommendations = relationship("ActionRecommendation", back_populates="shadow_purchase")
    behavior_metrics = relationship("BehaviorMetric", back_populates="shadow_purchase")
    user_feedback = relationship("UserFeedback", back_populates="shadow_purchase")
    audit_log = relationship("AuditLog", back_populates="shadow_purchase")


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


# ─── B4: Role-Based Access Control ───────────────────────────────
class UserRole(Base):
    """Maps usernames to roles for RBAC enforcement."""
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)  # "admin" | "analyst" | "auditor"
    created_at = Column(String, nullable=True)

# Role permission matrix — defines what each role can do
ROLE_PERMISSIONS = {
    "admin":   ["view_all", "resolve", "dismiss", "export", "retrain", "configure"],
    "analyst": ["view_all", "resolve", "dismiss", "export"],
    "auditor": ["view_all", "export"],  # Read-only + export, no state changes
}



# ─── F6: Vendor Contract Compliance ──────────────────────────────────
class VendorContract(Base):
    """Stores uploaded MSA/contract text for NLP compliance checking."""
    __tablename__ = "vendor_contracts"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id     = Column(String, ForeignKey("vendors.id"), nullable=False)
    contract_text = Column(Text, nullable=False)
    uploaded_at   = Column(String)
    active        = Column(Boolean, default=True)


# ─── F7: Digital Twin / IoT Inventory Sync ───────────────────────────
class InventoryItem(Base):
    """IoT-synced inventory items with reorder automation."""
    __tablename__ = "inventory_items"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    item_id             = Column(String, unique=True, nullable=False, index=True)
    name                = Column(String)
    quantity            = Column(Float, default=0)
    reorder_point       = Column(Float, default=10)    # triggers auto PO draft below this
    reorder_qty         = Column(Float, default=50)    # quantity to order on auto-draft
    unit                = Column(String, default="units")
    location            = Column(String, default="Warehouse A")
    preferred_vendor_id = Column(String, ForeignKey("vendors.id"), nullable=True)
    last_synced         = Column(String)               # ISO datetime of last IoT ping


class PurchaseOrderDraft(Base):
    """Auto-raised PO drafts for procurement team approval."""
    __tablename__ = "purchase_order_drafts"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id   = Column(String, ForeignKey("vendors.id"), nullable=True)
    item_name   = Column(String)
    quantity    = Column(Float)
    status      = Column(String, default="Draft")  # Draft, Approved, Rejected
    created_at  = Column(String)
    auto_raised = Column(Boolean, default=False)   # True = system-raised, not human


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
    timestamp = Column(String, nullable=False)  # ISO format
    action_type = Column(String, nullable=False)  # 'convert_to_po', 'flag_vendor', 'mark_justified', 'escalate_audit'
    user = Column(String, default="System Administrator")
    notes = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False)


# ==============================================================================
#  PREVENTIVE INTELLIGENCE LAYER - NEW TABLES
# ==============================================================================

class InventoryConfidence(Base):
    """Tracks per-item confidence score for the Preventive Intelligence Layer."""
    __tablename__ = "inventory_confidence"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, ForeignKey("inventory.id"), nullable=False, unique=True)
    confidence_score = Column(Float, default=50.0)          # 0-100 computed score
    last_verified = Column(String, nullable=True)            # ISO timestamp when last verified
    mismatch_count = Column(Integer, default=0)              # Number of historical mismatches
    verification_status = Column(String, default="unverified")  # unverified | partial | verified | mismatch_reported
    source = Column(String, default="ai_auto_update")        # ai_auto_update | manual
    
class VerificationTask(Base):
    """Tasks generated when confidence decays or user overrides an AI recommendation."""
    __tablename__ = "verification_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    location = Column(String, nullable=True)
    priority = Column(String, default="standard")  # standard | urgent
    reason = Column(String, nullable=True)
    requested_at = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | physically_confirmed
    verifier_id = Column(String, nullable=True)


class ConfidenceDecayLog(Base):
    """Log of automated confidence decay events."""
    __tablename__ = "confidence_decay_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    delta = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)


class RetrievalLog(Base):
    """Historical log of actual retrieval times for items."""
    __tablename__ = "retrieval_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, ForeignKey("inventory.id"), nullable=False)
    warehouse_location = Column(String, nullable=True)
    retrieval_time_minutes = Column(Float, nullable=False)   # Actual retrieval time
    logged_at = Column(String, nullable=False)               # ISO timestamp
    logged_by = Column(String, default="System")             # Who logged it


class EmergencyDecisionLog(Base):
    """Audit trail for every emergency decision the system makes."""
    __tablename__ = "emergency_decision_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, nullable=True)                  # Inventory item queried
    part_name = Column(String, nullable=False)               # Part name searched
    confidence_score = Column(Float, default=0.0)            # Score at time of decision
    retrieval_time = Column(Float, nullable=True)            # Estimated retrieval time
    decision = Column(String, nullable=False)                # "Use Internal Stock" | "Proceed with Procurement" etc
    reason = Column(Text, nullable=True)                     # Human-readable explanation
    user_proceeded = Column(Boolean, nullable=True)          # Did user follow recommendation?
    user_action = Column(String, nullable=True)              # "followed" | "overridden"
    logged_at = Column(String, nullable=False)               # ISO timestamp
    department = Column(String, nullable=True)               # Department making request
    severity = Column(String, default="safe")                # safe | caution | critical
    verification_result = Column(String, nullable=True)      # "Found" | "Missing" | "Partial"
    quantity_adjusted = Column(Integer, default=0)           # If manual check modified inventory
    estimated_cost_avoided = Column(Float, default=0.0)      # Added for Phase 6 metrics



class UnifiedEvent(Base):
    """Module 1: Unified Data Ingestion Layer for all operational signals."""
    __tablename__ = "unified_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, nullable=False)
    source = Column(String, nullable=False) # financial, maintenance, inventory, logistics, workforce
    timestamp = Column(String, nullable=False)
    machine_id = Column(String, nullable=True)
    location_id = Column(String, nullable=True)
    vendor_id = Column(String, nullable=True)
    raw_text = Column(Text, nullable=True)
    amount = Column(Float, nullable=True)
    item_guess = Column(String, nullable=True)
    evidence_strength = Column(Float, default=0.5)


class LivingRiskScore(Base):
    """Module 4: Dynamic Danger/Risk score."""
    __tablename__ = "living_risk_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, ForeignKey("inventory.id"), nullable=True)
    transaction_id = Column(String, nullable=True)
    risk_score = Column(Float, default=0.0)
    last_updated = Column(String, nullable=False)
    factors = Column(Text, nullable=True) # JSON of risk factors


class InventoryCorrectionLedger(Base):
    """Module 7: Immutable audit chain for inventory corrections."""
    __tablename__ = "inventory_corrections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, ForeignKey("inventory.id"), nullable=False)
    proposed_quantity_change = Column(Integer, nullable=False)
    status = Column(String, default="Pending") # Pending, Auto-posted, Review-required, Rolled-back
    evidence_source = Column(String, nullable=True)
    reason_code = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)
    version_id = Column(Integer, default=1)


class TrustMomentum(Base):
    """Module 8: Trust repair and behavior change tracking."""
    __tablename__ = "trust_momentum"
    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String, nullable=False)
    department = Column(String, nullable=False)
    trust_score = Column(Float, default=50.0)
    savings_metrics = Column(Float, default=0.0)
    downtime_avoided_hours = Column(Float, default=0.0)
    last_updated = Column(String, nullable=False)


# ==============================================================================
#  NETWORK MESH LAYER - NEW TABLES
# ==============================================================================

class InventoryLocations(Base):
    """Tracks inventory spread across multiple warehouses."""
    __tablename__ = "inventory_locations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String, ForeignKey("inventory.id"), nullable=False)
    warehouse_id = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    last_updated = Column(String, nullable=False)

class WarehouseTransferCosts(Base):
    """Tracks time and financial cost of moving parts between warehouses."""
    __tablename__ = "warehouse_transfer_costs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_warehouse = Column(String, nullable=False)
    destination_warehouse = Column(String, nullable=False)
    estimated_hours = Column(Float, nullable=False)
    transfer_cost = Column(Float, nullable=False)

class ShiftRoster(Base):
    """Models staff availability per warehouse."""
    __tablename__ = "shift_roster"
    id = Column(Integer, primary_key=True, autoincrement=True)
    warehouse_id = Column(String, nullable=False)
    shift_name = Column(String, nullable=False)
    staff_count = Column(Integer, default=0)
    start_time = Column(String, nullable=False) # e.g., "08:00"
    end_time = Column(String, nullable=False)   # e.g., "16:00"

class WarehouseAccess(Base):
    """Tracks which departments/users can access which warehouses."""
    __tablename__ = "warehouse_access"
    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String, nullable=False)
    warehouse_id = Column(String, nullable=False)
    access_level = Column(String, default="Standard")


# ==============================================================================
#  PHASE 3 TO 6 TABLES
# ==============================================================================

class PartsCompatibility(Base):
    __tablename__ = "parts_compatibility"
    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_sku = Column(String, nullable=False)
    substitute_sku = Column(String, nullable=False)
    compatibility_score = Column(Integer, default=100)
    validated_by = Column(String, default="unvalidated") # 'oem', 'engineer_approved', 'unvalidated'
    safe_for_critical = Column(Boolean, default=False)

class MachineCriticality(Base):
    __tablename__ = "machine_criticality"
    machine_id = Column(String, primary_key=True)
    criticality_level = Column(String, default="standard") # 'critical', 'high', 'standard'
    downtime_cost_per_hour = Column(Float, default=0.0)

class ItemSynonyms(Base):
    __tablename__ = "item_synonyms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_sku = Column(String, nullable=False)
    synonym = Column(String, nullable=False)
    source = Column(String, default="auto_learned") # 'manual', 'auto_learned'

class RiskScoreHistory(Base):
    __tablename__ = "risk_score_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=False)
    score = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)
    trigger_event = Column(String, nullable=False)

class MachineUsageLog(Base):
    __tablename__ = "machine_usage_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String, nullable=False)
    part_sku = Column(String, nullable=False)
    event_type = Column(String, nullable=False) # 'replacement', 'failure', 'scheduled_maintenance'
    event_date = Column(String, nullable=False) # ISO date
    quantity_used = Column(Integer, default=1)

class DepletionAlerts(Base):
    __tablename__ = "depletion_alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=False)
    predicted_need_date = Column(String, nullable=False) # ISO date
    confidence = Column(Float, default=0.0)
    suggested_order_qty = Column(Integer, default=0)
    status = Column(String, default="pending")
    created_at = Column(String, nullable=False) # ISO timestamp

class SignalEvents(Base):
    __tablename__ = "signal_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String, nullable=False) # 'gate_entry', 'petty_cash', 'dept_transfer'
    timestamp = Column(String, nullable=False) # ISO timestamp
    raw_data = Column(Text, nullable=False) # JSON data
    correlated_shadow_id = Column(Integer, ForeignKey("shadow_purchases.id"), nullable=True)

class UserTrustMetrics(Base):
    __tablename__ = "user_trust_metrics"
    user_id = Column(String, primary_key=True)
    total_checks = Column(Integer, default=0)
    followed_recommendations = Column(Integer, default=0)
    overrides_that_were_correct = Column(Integer, default=0)
    internal_retrievals_successful = Column(Integer, default=0)
    estimated_cost_saved = Column(Float, default=0.0)
    estimated_time_saved_minutes = Column(Integer, default=0)
    trust_score = Column(Float, default=50.0)


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

    # Inventory
    with open(os.path.join(data_dir, "inventory.csv")) as f:
        for row in csv.DictReader(f):
            db.add(Inventory(id=row["id"], name=row["name"], sku=row["sku"],
                             quantity=int(row["quantity"]), unit_price=float(row["unit_price"]),
                             category=row["category"], reorder_level=int(row["reorder_level"]),
                             location=row["location"]))

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

    # Seed Network Mesh Data
    from database import WarehouseTransferCosts, ShiftRoster
    if not db.query(WarehouseTransferCosts).first():
        db.add_all([
            WarehouseTransferCosts(source_warehouse="WH-Alpha", destination_warehouse="WH-Beta", estimated_hours=4.0, transfer_cost=150.0),
            WarehouseTransferCosts(source_warehouse="WH-Beta", destination_warehouse="WH-Alpha", estimated_hours=4.5, transfer_cost=165.0),
            WarehouseTransferCosts(source_warehouse="WH-Alpha", destination_warehouse="WH-Gamma", estimated_hours=12.0, transfer_cost=450.0)
        ])
    if not db.query(ShiftRoster).first():
        db.add_all([
            ShiftRoster(warehouse_id="WH-Alpha", shift_name="Morning", staff_count=5, start_time="06:00", end_time="14:00"),
            ShiftRoster(warehouse_id="WH-Alpha", shift_name="Evening", staff_count=2, start_time="14:00", end_time="22:00"),
            ShiftRoster(warehouse_id="WH-Beta", shift_name="Day", staff_count=8, start_time="08:00", end_time="18:00"),
            ShiftRoster(warehouse_id="WH-Beta", shift_name="Night", staff_count=0, start_time="18:00", end_time="08:00")
        ])

    from database import ItemSynonyms
    if not db.query(ItemSynonyms).first():
        db.add_all([
            ItemSynonyms(canonical_sku="SKU-BRG-6204", synonym="BRG-6204-ZZ", source="manual"),
            ItemSynonyms(canonical_sku="SKU-BRG-6204", synonym="bearing 6204", source="manual"),
            ItemSynonyms(canonical_sku="SKU-BRG-6204", synonym="deep groove ball bearing 20mm", source="manual"),
            ItemSynonyms(canonical_sku="SKU-BRG-6204", synonym="roulement 6204", source="manual")
        ])

    db.commit()
    db.close()
    print("[OK] Database initialized and seeded.")


if __name__ == "__main__":
    init_db()
