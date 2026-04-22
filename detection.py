"""
Shadow Detection Engine v3.0.
Matches financial transactions against procurement records.
Flags unmatched transactions as shadow purchases.
Uses multi-feature AI anomaly detection.
Includes: vendor trust scoring, risk metric snapshots, recommendation generation.
"""
from sqlalchemy.orm import Session
from database import (
    Transaction, Procurement, ShadowPurchase, Vendor, Inventory, 
    RiskSnapshot, RiskMetric, ActionRecommendation, BehaviorMetric
)
from ai_module import shadow_ai
import datetime


def run_detection(db: Session) -> dict:
    """
    Core detection pipeline:
    1. Extract data from structured database (simulates ERP extraction).
    2. For each transaction, match against POs (vendor + amount + date tolerance).
    3. Flag unmatched as shadow purchases.
    4. Run multi-feature AI anomaly scoring.
    5. Classify item category from description.
    6. Update vendor trust scores.
    7. Store risk metric snapshot.
    """
    transactions = db.query(Transaction).all()
    pos = db.query(Procurement).all()
    vendors_map = {v.name: v for v in db.query(Vendor).all()}

    # Build feature sets for AI training (ERP data extraction simulation)
    feature_sets = []
    for t in transactions:
        vendor_info = None
        v = vendors_map.get(t.vendor)
        if v:
            vendor_info = {"risk_level": v.risk_level, "approved": v.approved}
        features = shadow_ai.ingestion.extract_transaction_features(
            {"date": t.date, "amount": t.amount, "payment_type": t.payment_type, "card_holder": t.card_holder},
            vendor_info
        )
        feature_sets.append(features)

    shadow_ai.fit_anomaly_detector(feature_sets)

    new_shadows = 0
    matched = 0
    already_processed = 0

    for idx, txn in enumerate(transactions):
        if txn.matched_po_id or txn.is_shadow:
            already_processed += 1
            if txn.matched_po_id:
                matched += 1
            continue

        found_match = False
        for po in pos:
            if _is_match(txn, po):
                txn.matched_po_id = po.id
                txn.is_shadow = False
                found_match = True
                matched += 1
                break

        if not found_match:
            txn.is_shadow = True

            # ─── Multi-feature Enterprise AI Analysis ───────
            features = feature_sets[idx]
            risk_score = shadow_ai.get_anomaly_score(features)
            item_cat = shadow_ai.classify_item(txn.description)
            
            # 1. System Confidence Engine
            confidence = shadow_ai.calculate_confidence(features, txn.__dict__)
            
            # 2. XAI Layer (Explainable AI)
            anomaly_factors = shadow_ai.get_anomaly_breakdown(features)
            
            # 3. Financial Impact Engine
            vendor = vendors_map.get(txn.vendor)
            v_risk = vendor.risk_level if vendor else "High"
            impact = shadow_ai.calculate_risk_impact(txn.amount, risk_score, v_risk)
            
            # 4. Data Quality Flagging
            dq_flag = shadow_ai.get_data_quality(txn.__dict__)
            
            # 5. Action Recommendation Engine
            recommendation = shadow_ai.generate_action_recommendation(risk_score, confidence, features)

            txn.ai_risk_score = risk_score
            txn.ai_category = item_cat

            existing = db.query(ShadowPurchase).filter(
                ShadowPurchase.transaction_id == txn.id
            ).first()
            
            if not existing:
                # Create main ShadowPurchase record
                new_shadow = ShadowPurchase(
                    transaction_id=txn.id,
                    detected_at=datetime.date.today().isoformat(),
                    reason=" | ".join(anomaly_factors),
                    risk_score=risk_score,
                    confidence_score=confidence,
                    data_quality_flag=dq_flag,
                    status="Pending",
                    item_category=item_cat,
                )
                db.add(new_shadow)
                db.flush() # Get ID
                
                # Create RiskMetric record
                db.add(RiskMetric(
                    transaction_id=txn.id,
                    risk_score=risk_score,
                    estimated_loss=impact["estimated_loss"],
                    category=impact["category"]
                ))
                
                # Create Recommendation record
                db.add(ActionRecommendation(
                    transaction_id=txn.id,
                    recommendation_text=recommendation,
                    priority=impact["category"] # Use risk category as priority
                ))
                
                # Update Behavioral Metrics
                _update_behavior_metrics(db, txn, impact["category"])
                
                new_shadows += 1

    # Update vendor trust scores
    _update_vendor_trust_scores(db, vendors_map)

    db.commit()

    # Store aggregate risk snapshot
    risk_snapshot = _compute_risk_snapshot(db)
    db.add(RiskSnapshot(**risk_snapshot))
    
    # Store dynamic trends for telemetry dashboards
    _update_trend_metrics(db, risk_snapshot)
    
    db.commit()

    total_shadows = db.query(ShadowPurchase).count()
    pending = db.query(ShadowPurchase).filter(ShadowPurchase.status == "Pending").count()

    return {
        "new_detections": new_shadows,
        "total_shadows": total_shadows,
        "pending": pending,
        "matched_transactions": matched,
        "already_processed": already_processed,
        "risk_snapshot": risk_snapshot,
    }


def resolve_shadow_purchase(db: Session, shadow_id: int, po_id: str = None) -> dict:
    """Convert shadow purchase → formal procurement record + update inventory (OPTIMIZED)."""
    # Single query for shadow
    shadow = db.query(ShadowPurchase).filter(ShadowPurchase.id == shadow_id).first()
    if not shadow:
        return {"status": "error", "error": f"Shadow purchase {shadow_id} not found"}
    if shadow.status == "Resolved":
        return {"status": "error", "error": "Shadow purchase is already resolved"}

    # Single query for transaction
    txn = db.query(Transaction).filter(Transaction.id == shadow.transaction_id).first()
    if not txn:
        return {"status": "error", "error": f"Transaction {shadow.transaction_id} not found"}

    # Single query for vendor (no vendor creation logic - keep it simple)
    vendor = db.query(Vendor).filter(Vendor.name == txn.vendor).first()
    if not vendor:
        vendor = Vendor(
            id=f"V{str(db.query(Vendor).count() + 1).zfill(3)}",
            name=txn.vendor, category="General Hardware",
            risk_level="High", approved=False, avg_order=txn.amount,
            trust_score=15.0,
        )
        db.add(vendor)

    # Generate PO ID efficiently
    if not po_id:
        po_count = db.query(Procurement).count()
        new_po_id = f"PO-{str(po_count + 1).zfill(3)}"
    else:
        existing_po = db.query(Procurement).filter(Procurement.id == po_id).first()
        if existing_po:
            return {"status": "error", "error": f"PO ID {po_id} already exists"}
        new_po_id = po_id

    item_cat = shadow.item_category or shadow_ai.classify_item(txn.description)

    # Single add for procurement
    db.add(Procurement(
        id=new_po_id, vendor_id=vendor.id, vendor_name=vendor.name,
        item=txn.description, amount=txn.amount, quantity=1,
        date=txn.date, status="Resolved (Shadow-to-PO)",
        department=txn.department, source="Shadow-Resolved",
    ))

    # OPTIMIZED inventory update - use indexed lookup instead of full table scan
    inv_result = _update_inventory_optimized(db, txn, item_cat)

    # Batch update all changes
    shadow.status = "Resolved"
    shadow.resolved_po_id = new_po_id
    txn.is_shadow = False
    txn.matched_po_id = new_po_id

    # Update vendor trust
    if vendor:
        vendor.trust_score = min(100, vendor.trust_score + 2)

    # SINGLE commit for all changes
    db.commit()
    return {
        "status": "success",
        "po_id": new_po_id,
        "item_category": item_cat,
        "vendor": vendor.name,
        "amount": txn.amount,
        "inventory_update": inv_result,
    }


def resolve_all_vendor_shadows(db: Session, vendor_name: str) -> dict:
    """Bulk resolve all pending shadows for a specific vendor."""
    from sqlalchemy import and_
    shadows = db.query(ShadowPurchase).join(
        Transaction, ShadowPurchase.transaction_id == Transaction.id
    ).filter(
        and_(
            Transaction.vendor == vendor_name,
            ShadowPurchase.status == "Pending"
        )
    ).all()
    
    count = 0
    results = []
    for s in shadows:
        res = resolve_shadow_purchase(db, s.id)
        if res.get("status") == "success":
            count += 1
            results.append(res["po_id"])
            
    return {
        "status": "success",
        "count": count,
        "po_ids": results,
        "vendor": vendor_name
    }



def dismiss_shadow_purchase(db: Session, shadow_id: int) -> dict:
    """Mark shadow purchase as Ignored without creating a PO."""
    shadow = db.query(ShadowPurchase).filter(ShadowPurchase.id == shadow_id).first()
    if not shadow:
        return {"status": "error", "error": f"Shadow purchase {shadow_id} not found"}
    
    txn = db.query(Transaction).filter(Transaction.id == shadow.transaction_id).first()
    if txn:
        txn.is_shadow = False
        txn.matched_po_id = "DISMISSED"
    
    shadow.status = "Ignored"
    db.commit()
    return {"status": "success", "message": f"Shadow purchase {shadow_id} dismissed"}


def get_recommendations(db: Session) -> list[dict]:
    """Generate AI-powered decision recommendations."""
    shadows = db.query(ShadowPurchase).filter(ShadowPurchase.status == "Pending").all()
    vendors = {v.name: v for v in db.query(Vendor).all()}
    transactions = {t.id: t for t in db.query(Transaction).all()}
    return shadow_ai.generate_recommendations(shadows, vendors, transactions)


def _is_match(txn: Transaction, po: Procurement) -> bool:
    """Match transaction to PO by vendor + amount (±5%) + date (±7 days)."""
    v1, v2 = txn.vendor.lower(), po.vendor_name.lower()
    if v1 not in v2 and v2 not in v1:
        return False
    if abs(txn.amount - po.amount) > po.amount * 0.05:
        return False
    try:
        t_date = datetime.date.fromisoformat(str(txn.date)[:10])
        p_date = datetime.date.fromisoformat(str(po.date)[:10])
        if abs((t_date - p_date).days) > 7:
            return False
    except (ValueError, TypeError):
        return False
    return True


def _update_inventory_optimized(db: Session, txn: Transaction, category: str) -> dict:
    """OPTIMIZED: Use category-based lookup instead of full table scan."""
    from sqlalchemy import or_
    
    # Try exact category match first (indexed lookup)
    matching_items = db.query(Inventory).filter(Inventory.category == category).all()
    
    if matching_items:
        # Match by description keywords on subset, not full table
        desc_words = set(w.lower() for w in txn.description.split() if len(w) > 3)
        for item in matching_items:
            item_words = set(w.lower() for w in item.name.split() if len(w) > 3)
            if desc_words & item_words:
                item.quantity += 1
                item.last_updated = datetime.datetime.now().isoformat()
                return {"action": "updated", "item": item.name, "new_qty": item.quantity}
    
    # Create new if no match
    inv_count = db.query(Inventory).count()
    new_item = Inventory(
        id=f"INV{str(inv_count + 1).zfill(3)}",
        name=txn.description[:50], sku=f"SHD-{txn.id}",
        quantity=1, unit_price=txn.amount,
        category=category, reorder_level=5, location="Receiving Dock",
        last_updated=datetime.datetime.now().isoformat()
    )
    db.add(new_item)
    return {"action": "created", "item": new_item.name, "new_qty": 1}


def _update_inventory(db: Session, txn: Transaction, category: str) -> dict:
    """Legacy function - now redirects to optimized version."""
    return _update_inventory_optimized(db, txn, category)


def get_inventory_reorders(db: Session) -> list:
    """
    REAL-TIME REORDER DETECTION
    Analyzes inventory levels and returns items that need reordering.
    Considers: current quantity, reorder level, and usage trends
    """
    items_needing_reorder = []
    
    for item in db.query(Inventory).all():
        # Get last 10 transactions for this item
        recent_txns = db.query(Transaction).filter(
            Transaction.description.ilike(f"%{item.name}%")
        ).order_by(Transaction.date.desc()).limit(10).all()
        
        # Calculate usage trend
        usage_count = len(recent_txns)
        avg_usage_per_day = usage_count / max(1, 10)  # Approximate based on 10 samples
        
        # Predict stocking need
        days_until_empty = item.quantity / max(avg_usage_per_day, 0.1) if item.quantity > 0 else 0
        
        # Flag for reorder if:
        # 1. Below reorder level, OR
        # 2. Less than 7 days of stock, OR
        # 3. High usage with low quantity
        should_reorder = (
            item.quantity <= item.reorder_level or 
            days_until_empty < 7 or
            (avg_usage_per_day > 0.5 and item.quantity < 10)
        )
        
        if should_reorder:
            suggested_qty = max(20, int(avg_usage_per_day * 30))  # 30 days of stock
            items_needing_reorder.append({
                "id": item.id,
                "name": item.name,
                "current_qty": item.quantity,
                "reorder_level": item.reorder_level,
                "category": item.category,
                "last_updated": getattr(item, 'last_updated', 'N/A'),
                "avg_daily_usage": round(avg_usage_per_day, 2),
                "days_until_empty": round(days_until_empty, 1),
                "suggested_order_qty": suggested_qty,
                "urgency": "CRITICAL" if item.quantity == 0 else "HIGH" if item.quantity <= item.reorder_level else "MEDIUM"
            })
    
    return sorted(items_needing_reorder, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}[x["urgency"]])


def create_inventory_reorder(db: Session, item_id: str, order_qty: int, vendor_name: str = "Standard Supplier") -> dict:
    """
    Create a reorder procurement record for a low-stock inventory item.
    Automatically generates PO and updates inventory expectations.
    """
    item = db.query(Inventory).filter(Inventory.id == item_id).first()
    if not item:
        return {"status": "error", "error": f"Inventory item {item_id} not found"}
    
    # Find or create vendor
    vendor = db.query(Vendor).filter(Vendor.name == vendor_name).first()
    if not vendor:
        vendor = Vendor(
            id=f"V{str(db.query(Vendor).count() + 1).zfill(3)}",
            name=vendor_name, category=item.category,
            risk_level="Low", approved=True, avg_order=item.unit_price * order_qty,
            trust_score=80.0,
        )
        db.add(vendor)
    
    # Create procurement record
    po_count = db.query(Procurement).count()
    new_po_id = f"PO-REORDER-{str(po_count + 1).zfill(3)}"
    
    reorder_po = Procurement(
        id=new_po_id,
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        item=item.name,
        amount=item.unit_price * order_qty,
        quantity=order_qty,
        date=datetime.date.today().isoformat(),
        status="Reorder Pending",
        department="Inventory Management",
        source="Auto-Reorder"
    )
    db.add(reorder_po)
    
    # Update inventory with expected arrival
    item.quantity += order_qty  # Mark as on-order (will be received)
    item.last_updated = datetime.datetime.now().isoformat()
    
    db.commit()
    
    return {
        "status": "success",
        "po_id": new_po_id,
        "item_id": item_id,
        "item_name": item.name,
        "order_qty": order_qty,
        "vendor": vendor.name,
        "total_cost": item.unit_price * order_qty,
        "new_expected_qty": item.quantity,
        "message": f"Reorder created for {order_qty} units of {item.name}"
    }


def monitor_inventory_trends(db: Session, days: int = 30) -> dict:
    """
    TREND ANALYSIS
    Analyzes inventory movements over time to identify usage patterns
    and predict future reorder needs.
    """
    trends = {
        "high_usage_items": [],
        "low_usage_items": [],
        "stable_items": [],
        "at_risk_items": [],
        "summary": {
            "total_items": 0,
            "items_needing_reorder": 0,
            "total_value": 0.0,
            "average_turnover": 0.0
        }
    }
    
    items = db.query(Inventory).all()
    trends["summary"]["total_items"] = len(items)
    
    for item in items:
        # Calculate usage
        txn_count = db.query(Transaction).filter(
            Transaction.description.ilike(f"%{item.name}%")
        ).count()
        
        avg_daily_usage = txn_count / max(days, 1)
        item_value = item.unit_price * item.quantity
        trends["summary"]["total_value"] += item_value
        
        item_data = {
            "id": item.id,
            "name": item.name,
            "current_qty": item.quantity,
            "reorder_level": item.reorder_level,
            "unit_price": item.unit_price,
            "total_value": item_value,
            "total_transactions": txn_count,
            "avg_daily_usage": round(avg_daily_usage, 2),
        }
        
        # Categorize by usage
        if avg_daily_usage > 0.5:
            trends["high_usage_items"].append(item_data)
        elif avg_daily_usage > 0.1:
            trends["stable_items"].append(item_data)
        else:
            trends["low_usage_items"].append(item_data)
        
        # Identify at-risk items
        if item.quantity <= item.reorder_level:
            trends["at_risk_items"].append({**item_data, "status": "CRITICAL - Below reorder level"})
    
    trends["summary"]["items_needing_reorder"] = len(trends["at_risk_items"])
    trends["summary"]["average_turnover"] = round(
        sum(i["total_transactions"] for i in items) / max(len(items), 1), 2
    )
    
    return trends


def _update_vendor_trust_scores(db: Session, vendors_map: dict):
    """Dynamically update vendor trust scores based on shadow purchase patterns."""
    for name, vendor in vendors_map.items():
        shadow_count = db.query(ShadowPurchase).join(
            Transaction, ShadowPurchase.transaction_id == Transaction.id
        ).filter(Transaction.vendor == name, ShadowPurchase.status == "Pending").count()

        # Decrease trust for vendors with pending shadows
        if shadow_count > 0:
            penalty = min(shadow_count * 5, 30)
            vendor.trust_score = max(0, vendor.trust_score - penalty * 0.1)
            if vendor.trust_score < 25:
                vendor.risk_level = "High"
            elif vendor.trust_score < 55:
                vendor.risk_level = "Medium"
        else:
            # Slowly recover trust
            vendor.trust_score = min(100, vendor.trust_score + 0.5)
            if vendor.trust_score > 70:
                vendor.risk_level = "Low"


def _update_behavior_metrics(db: Session, txn: Transaction, risk_level: str):
    """Track patterns for accountability analysis."""
    employee = txn.card_holder or "Unknown"
    dept = txn.department or "Unknown"
    
    # Employee level
    beh = db.query(BehaviorMetric).filter(BehaviorMetric.employee_id == employee).first()
    if not beh:
        beh = BehaviorMetric(employee_id=employee, department=dept, shadow_count=0)
        db.add(beh)
    beh.shadow_count += 1
    if risk_level in ["High", "Critical"]:
        beh.risk_level = risk_level


def _compute_risk_snapshot(db: Session) -> dict:
    """Compute current risk aggregate snapshot."""
    total_txn = db.query(Transaction).count()
    shadows = db.query(ShadowPurchase).all()
    pending = [s for s in shadows if s.status == "Pending"]

    total_exposure = 0
    risk_scores = []
    for s in pending:
        # Use the new RiskMetric table for exposure value
        m = db.query(RiskMetric).filter(RiskMetric.transaction_id == s.transaction_id).first()
        if m:
            total_exposure += m.estimated_loss
        risk_scores.append(s.risk_score or 0)

    shadow_rate = len(shadows) / max(total_txn, 1)
    avg_risk = sum(risk_scores) / max(len(risk_scores), 1)
    high_risk = sum(1 for r in risk_scores if r > 0.6)

    if avg_risk > 0.6 or total_exposure > 10000:
        level = "Critical"
    elif avg_risk > 0.4 or total_exposure > 5000:
        level = "High"
    elif avg_risk > 0.2:
        level = "Medium"
    else:
        level = "Low"

    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_exposure": round(total_exposure, 2),
        "shadow_rate": round(shadow_rate, 4),
        "avg_risk_score": round(avg_risk, 4),
        "high_risk_count": high_risk,
        "risk_level": level,
        "pending_actions": len(pending),
    }


def _update_trend_metrics(db: Session, snapshot: dict):
    """Store time-series data for the Nexus Telemetry Grid."""
    from database import TrendMetric
    from sqlalchemy import func
    
    today = datetime.date.today().isoformat()
    
    # 1. Total Risk Exposure Trend
    db.add(TrendMetric(
        date=today,
        metric_type="shadow_count",
        value=float(snapshot["pending_actions"]),
        details="Count of active unauthorized procurement flags."
    ))
    
    # 2. Financial Exposure Trend
    db.add(TrendMetric(
        date=today,
        metric_type="financial_exposure",
        value=float(snapshot["total_exposure"]),
        details="Monetary risk value in USD."
    ))
    
    # 3. Departmental Variance (High Risk Concentration)
    from database import Transaction
    dept_risk = db.query(
        Transaction.department,
        func.count(Transaction.id)
    ).filter(Transaction.is_shadow == True).group_by(Transaction.department).all()
    
    for dept, count in dept_risk:
        if dept:
            db.add(TrendMetric(
                date=today,
                metric_type="department_activity",
                value=float(count),
                category=dept,
                details=f"Shadow purchases detected in {dept}"
            ))
