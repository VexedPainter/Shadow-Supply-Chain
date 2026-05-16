"""
analytics.py — ShadowSync Analytics Engine
===========================================
Department-level predictive risk scoring, spend analysis utilities.
Kept separate from ai_module.py (ML) and ai_copilot.py (LLM calls).
"""
from __future__ import annotations
import datetime
from typing import Optional


def predict_department_risk(db, dept: str) -> dict:
    """
    Predict future shadow spend risk for a given department based on
    the last 90 transactions. Lightweight — no ML inference required.

    Risk formula:
        score = (shadow_rate × 0.6) + (weekend_rate × 0.2) + (avg_amount_factor × 0.2)

    Returns None for predicted_risk if fewer than 10 transactions exist.
    """
    from database import Transaction

    rows = (
        db.query(Transaction)
        .filter(Transaction.department == dept)
        .order_by(Transaction.date.desc())
        .limit(90)
        .all()
    )

    if len(rows) < 10:
        return {
            "department":      dept,
            "predicted_risk":  None,
            "shadow_rate_30d": None,
            "avg_amount":      None,
            "transaction_count": len(rows),
            "recommendation":  "Insufficient data (need 10+ transactions)",
        }

    shadow_rate  = sum(1 for r in rows if r.is_shadow) / len(rows)
    avg_amount   = sum(r.amount or 0 for r in rows) / len(rows)

    # Weekend rate — check date string's day-of-week
    weekend_count = 0
    for r in rows:
        try:
            dt = datetime.date.fromisoformat(str(r.date)[:10])
            if dt.weekday() >= 5:
                weekend_count += 1
        except (ValueError, TypeError):
            pass
    weekend_rate = weekend_count / len(rows)

    risk_score = (
        shadow_rate  * 0.6 +
        weekend_rate * 0.2 +
        min(avg_amount / 50_000, 1.0) * 0.2
    )

    if risk_score > 0.6:
        recommendation = "Mandatory PO pre-approval required"
    elif risk_score > 0.4:
        recommendation = "Increase audit frequency"
    else:
        recommendation = "Continue monitoring"

    return {
        "department":        dept,
        "predicted_risk":    round(risk_score, 3),
        "shadow_rate_30d":   round(shadow_rate * 100, 1),
        "avg_amount":        round(avg_amount, 2),
        "weekend_rate":      round(weekend_rate * 100, 1),
        "transaction_count": len(rows),
        "recommendation":    recommendation,
    }
