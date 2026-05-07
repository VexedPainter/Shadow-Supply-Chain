import asyncio
import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, ShadowPurchase, DepletionAlerts, MachineUsageLog, Inventory, LivingRiskScore

def recalibrate_detection_logic(db: Session):
    """
    LP-01: Recalibrate detection weights based on human overrides.
    Finds shadow purchases that were false positives and adjusts risk models.
    """
    false_positives = db.query(ShadowPurchase).filter(
        ShadowPurchase.confirmed_shadow == False,
        ShadowPurchase.risk_score > 0.7
    ).all()
    
    for fp in false_positives:
        fp.risk_score = max(0.1, fp.risk_score - 0.2)
    
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
