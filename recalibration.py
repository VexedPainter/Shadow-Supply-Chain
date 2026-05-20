import asyncio
import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, ShadowPurchase, DepletionAlerts, MachineUsageLog, Inventory, LivingRiskScore

def recalibrate_detection_logic(db: Session):
    """
    LP-01: Recalibrate risk scores based on human reviewer verdicts.

    IDEMPOTENCY FIX: Previous version re-applied score adjustments on EVERY
    hourly run with no guard, causing unbounded score drift (false positives
    converged to 0.1 in hours; confirmed shadows exceeded 1.0).
    Fix: filter on recalibration_applied == False so each verdict is processed
    exactly once, persisted in the DB and safe across server restarts.
    """
    # Only process records not yet recalibrated
    false_positives = db.query(ShadowPurchase).filter(
        ShadowPurchase.reviewer_verdict == "false_positive",
        ShadowPurchase.recalibration_applied == False,
    ).all()
    for fp in false_positives:
        fp.risk_score = max(0.1, fp.risk_score - 0.1)  # symmetric ±0.1 — prevents asymmetric score drift
        fp.recalibration_applied = True  # never re-process

    confirmed = db.query(ShadowPurchase).filter(
        ShadowPurchase.reviewer_verdict == "confirmed_shadow",
        ShadowPurchase.recalibration_applied == False,
    ).all()
    for cs in confirmed:
        cs.risk_score = min(1.0, cs.risk_score + 0.1)  # symmetric ±0.1 steps
        cs.recalibration_applied = True

    db.commit()

def run_predictive_depletion(db: Session):
    """
    LP-11/LP-07: Predictive depletion scanning based on MachineUsageLog.

    N+1 FIX: Previous version queried MachineUsageLog once per inventory item.
    Fix: load all recent usage records in one query, group them in Python by SKU.

    EDGE CASE FIX: items with quantity=0 produced a 0-day alert whose predicted
    date was 'today', creating noise.  Now guarded with `item.quantity > 0`.
    """
    items = db.query(Inventory).filter(Inventory.sku.isnot(None)).all()
    if not items:
        return

    thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()

    # N+1 FIX: single bulk query then group by SKU in Python
    all_usage = db.query(MachineUsageLog).filter(
        MachineUsageLog.event_date >= thirty_days_ago
    ).all()

    # Group usage records by SKU for O(1) lookup per item
    usage_by_sku: dict = {}
    for u in all_usage:
        usage_by_sku.setdefault(u.part_sku, []).append(u)

    for item in items:
        usage = usage_by_sku.get(item.sku, [])
        if not usage:
            continue

        total_used = sum(u.quantity_used for u in usage)
        daily_run_rate = total_used / 30.0

        if daily_run_rate <= 0:
            continue

        # EDGE CASE FIX: skip items already at zero — 0/rate=0 days is noise not insight
        if item.quantity <= 0:
            continue

        days_until_depleted = item.quantity / daily_run_rate
        if days_until_depleted < 14:
            existing = db.query(DepletionAlerts).filter(
                DepletionAlerts.sku == item.sku,
                DepletionAlerts.status == 'pending'
            ).first()
            if not existing:
                pred_date = (
                    datetime.datetime.now() + datetime.timedelta(days=days_until_depleted)
                ).isoformat()
                db.add(DepletionAlerts(
                    sku=item.sku,
                    predicted_need_date=pred_date[:10],
                    confidence=min(0.95, 0.5 + (len(usage) * 0.05)),
                    suggested_order_qty=max(1, int(daily_run_rate * 30)),
                    status='pending',
                    created_at=datetime.datetime.now().isoformat()
                ))
    db.commit()

async def intelligence_background_loop():
    """Background task runner for Phase 4."""
    while True:
        try:
            db = SessionLocal()
            try:
                recalibrate_detection_logic(db)
                run_predictive_depletion(db)
            finally:
                db.close()
        except Exception as e:
            print(f"[Intelligence Error] {e}")
        await asyncio.sleep(3600)  # Run every hour
