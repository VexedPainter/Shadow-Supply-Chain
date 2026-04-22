"""
Database models and initialization for Shadow Supply Chain system v3.0.
Uses SQLAlchemy ORM with SQLite.
Includes: RiskSnapshot, RiskMetric, ActionRecommendation, BehaviorMetric, and UserFeedback.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
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
    status = Column(String, default="Pending")         # Pending, Resolved, Ignored
    resolved_po_id = Column(String, nullable=True)
    item_category = Column(String, nullable=True)

    # Priority Queue Engine fields - NEW
    priority_score = Column(Float, default=0.0)        # Calculated priority score
    estimated_loss = Column(Float, default=0.0)       # Financial impact estimate
    frequency = Column(Integer, default=1)            # Pattern frequency count

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

    db.commit()
    db.close()
    print("[OK] Database initialized and seeded.")


if __name__ == "__main__":
    init_db()
