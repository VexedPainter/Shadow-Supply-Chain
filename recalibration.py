import asyncio
import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, ShadowPurchase, DepletionAlerts, MachineUsageLog, Inventory, LivingRiskScore

def recalibrate_detection_logic(db: Session):
    """
    LP-01: Recalibrate detection weights based on human reviewer verdicts.
    Uses reviewer_verdict field (set via /api/shadows/{id}/feedback) to find
    confirmed false positives and adjust risk scores accordingly.

    Bug fix: Previous version queried `confirmed_shadow == False AND risk_score > 0.7`,
    which incorrectly included ALL unreviewed high-score shadows.  The correct
    filter is `reviewer_verdict == 'false_positive'` so only human-labelled
    false positives trigger a score reduction.
    """
    # Only touch items that a human has explicitly labelled as false positives
    false_positives = db.query(ShadowPurchase).filter(
        ShadowPurchase.reviewer_verdict == "false_positive"
    ).all()

    for fp in false_positives:
        # Reduce the stored risk score so future aggregations are accurate.
        # Cap at 0.1 to retain a minimal signal for audit purposes.
        fp.risk_score = max(0.1, fp.risk_score - 0.2)

    # Also handle confirmed shadows: reinforce high scores
    confirmed = db.query(ShadowPurchase).filter(
        ShadowPurchase.reviewer_verdict == "confirmed_shadow"
    ).all()
    for cs in confirmed:
        cs.risk_score = min(1.0, cs.risk_score + 0.05)

    db.commit()

def run_predictive_depletion(db: Session):
    """
    LP-11/LP-07: Predictive depletion scanning based on MachineUsageLog.
    Calculates run rate for parts and creates DepletionAlerts.
    """
    items = db.query(Inventory).all()
    for item in items:
        if not item.sku:
            continue
            
        thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        usage = db.query(MachineUsageLog).filter(
            MachineUsageLog.part_sku == item.sku,
            MachineUsageLog.event_date >= thirty_days_ago
        ).all()
        
        if usage:
            total_used = sum(u.quantity_used for u in usage)
            daily_run_rate = total_used / 30.0
            
            if daily_run_rate > 0:
                days_until_depleted = item.quantity / daily_run_rate
                if days_until_depleted < 14: # Alert if less than 14 days
                    alert = db.query(DepletionAlerts).filter(DepletionAlerts.sku == item.sku, DepletionAlerts.status == 'pending').first()
                    if not alert:
                        pred_date = (datetime.datetime.now() + datetime.timedelta(days=days_until_depleted)).isoformat()
                        alert = DepletionAlerts(
                            sku=item.sku,
                            predicted_need_date=pred_date[:10],
                            confidence=min(0.95, 0.5 + (len(usage) * 0.05)),
                            suggested_order_qty=max(1, int(daily_run_rate * 30)), # 1 month supply
                            status='pending',
                            created_at=datetime.datetime.now().isoformat()
                        )
                        db.add(alert)
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
