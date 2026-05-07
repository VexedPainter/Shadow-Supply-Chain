"""
ShadowSync AI — LP Endpoints (v4.0)
All new endpoints for LP-01 through LP-12.
These are appended to app.py at build time.
"""

# ─────────────────────────────────────────────
# LP-01: Feedback Verdict & Retraining
# ─────────────────────────────────────────────

class ShadowVerdictRequest(BaseModel):
    verdict: str  # confirmed_shadow | false_positive | needs_review
    reviewer_id: str = "analyst_001"


@app.post("/api/shadows/{shadow_id}/feedback")
def submit_shadow_verdict(shadow_id: int, body: ShadowVerdictRequest,
                          user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-01: Human reviewer submits a verdict on a shadow detection."""
    shadow = db.query(ShadowPurchase).filter(ShadowPurchase.id == shadow_id).first()
    if not shadow:
        raise HTTPException(status_code=404, detail="Shadow not found")

    shadow.reviewer_verdict = body.verdict
    shadow.reviewed_at = datetime.datetime.now().isoformat()
    shadow.reviewer_id = body.reviewer_id

    # Update detection threshold for this vendor pattern
    txn = db.query(Transaction).filter(Transaction.id == shadow.transaction_id).first()
    if txn:
        threshold = db.query(DetectionThreshold).filter(
            DetectionThreshold.vendor_pattern == txn.vendor
        ).first()
        if not threshold:
            threshold = DetectionThreshold(vendor_pattern=txn.vendor, updated_at=datetime.datetime.now().isoformat())
            db.add(threshold)

        if body.verdict == "false_positive":
            threshold.false_positive_count += 1
            # Lower anomaly weight if FP rate is high
            total = threshold.false_positive_count + threshold.confirmed_shadow_count
            fp_rate = threshold.false_positive_count / max(total, 1)
            if fp_rate > 0.3:
                threshold.anomaly_weight = max(0.3, threshold.anomaly_weight - 0.1)
        elif body.verdict == "confirmed_shadow":
            threshold.confirmed_shadow_count += 1
        threshold.updated_at = datetime.datetime.now().isoformat()

    db.commit()
    _log_event(db, "LP01_VERDICT", str(shadow_id), f"Verdict: {body.verdict} by {body.reviewer_id}")
    return {"status": "success", "verdict_recorded": body.verdict}


# ─────────────────────────────────────────────
# LP-02: Confidence Decay & Verification Tasks
# ─────────────────────────────────────────────

@app.get("/api/verification-tasks")
def get_verification_tasks(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-02: Return pending warehouse verification tasks."""
    tasks = db.query(VerificationTask).filter(VerificationTask.status == "pending").all()
    return [{"id": t.id, "sku": t.sku, "location": t.location, "priority": t.priority,
             "reason": t.reason, "requested_at": t.requested_at} for t in tasks]


class VerifyInventoryRequest(BaseModel):
    confirmed_quantity: int
    location: str
    verifier_id: str = "warehouse_staff"


@app.post("/api/inventory/{sku}/verify")
def verify_inventory(sku: str, body: VerifyInventoryRequest,
                     user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-02: Staff confirms physical quantity, resets confidence."""
    inv = db.query(Inventory).filter(Inventory.sku == sku).first()
    if not inv:
        raise HTTPException(status_code=404, detail="SKU not found")

    inv.quantity = body.confirmed_quantity
    inv.last_updated = datetime.datetime.now().isoformat()

    # Resolve verification task
    task = db.query(VerificationTask).filter(
        VerificationTask.sku == sku, VerificationTask.status == "pending"
    ).first()
    if task:
        task.status = "confirmed"
        task.confirmed_quantity = body.confirmed_quantity
        task.verifier_id = body.verifier_id
        task.resolved_at = datetime.datetime.now().isoformat()

    # Update multi-location table
    loc = db.query(InventoryLocation).filter(
        InventoryLocation.sku == sku, InventoryLocation.warehouse_id == body.location
    ).first()
    if loc:
        loc.quantity = body.confirmed_quantity
        loc.confidence_score = min(100.0, loc.confidence_score + 20)
        loc.last_verified = datetime.datetime.now().isoformat()

    db.commit()
    _log_event(db, "LP02_VERIFIED", sku, f"Confirmed qty={body.confirmed_quantity} by {body.verifier_id}")
    return {"status": "verified", "sku": sku, "confirmed_quantity": body.confirmed_quantity}


# ─────────────────────────────────────────────
# LP-03: Multi-Signal Ingestion
# ─────────────────────────────────────────────

class GateEntrySignal(BaseModel):
    vendor: str
    delivery_note: str = ""
    location: str = "Main Gate"

class PettyCashSignal(BaseModel):
    amount: float
    category: str
    description: str
    requester: str

class DeptTransferSignal(BaseModel):
    from_dept: str
    to_dept: str
    item_description: str
    qty: int = 1


def _create_signal(db, source_type: str, raw_data: dict, flagged: bool = False):
    evt = SignalEvent(
        source_type=source_type,
        timestamp=datetime.datetime.now().isoformat(),
        raw_data=json.dumps(raw_data),
        flagged=flagged,
        evidence_strength=2 if flagged else 1
    )
    db.add(evt)
    db.commit()
    return evt


@app.post("/api/signals/gate-entry")
def ingest_gate_entry(body: GateEntrySignal, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-03: Register a vendor gate entry signal."""
    # Check if same vendor has a recent card transaction within ±2 hours
    cutoff = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
    recent = db.query(Transaction).filter(
        Transaction.vendor.ilike(f"%{body.vendor}%"),
        Transaction.date >= cutoff
    ).first()
    flagged = recent is not None
    evt = _create_signal(db, "gate_entry", body.dict(), flagged)
    return {"status": "recorded", "signal_id": evt.id, "flagged": flagged,
            "message": "⚠️ Matched recent card transaction — shadow signal raised" if flagged else "Logged"}


@app.post("/api/signals/petty-cash")
def ingest_petty_cash(body: PettyCashSignal, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-03: Register a petty cash spend signal."""
    flagged = body.amount > 500 and body.category.lower() in ["maintenance", "repair", "parts"]
    evt = _create_signal(db, "petty_cash", body.dict(), flagged)
    return {"status": "recorded", "signal_id": evt.id, "flagged": flagged}


@app.post("/api/signals/dept-transfer")
def ingest_dept_transfer(body: DeptTransferSignal, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-03: Register a department-to-department item transfer."""
    evt = _create_signal(db, "dept_transfer", body.dict(), flagged=False)
    return {"status": "recorded", "signal_id": evt.id}


# ─────────────────────────────────────────────
# LP-04: Parts Compatibility Safety Gate
# ─────────────────────────────────────────────

@app.get("/api/parts/{sku}/substitute")
def get_safe_substitute(sku: str, machine_id: str = "MACH-003",
                        user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-04: Return OEM-validated substitute with criticality gate."""
    machine = db.query(MachineCriticality).filter(MachineCriticality.machine_id == machine_id).first()
    criticality = machine.criticality_level if machine else "standard"

    substitutes = db.query(PartsCompatibility).filter(PartsCompatibility.primary_sku == sku).all()
    if not substitutes:
        return {"substitute": None, "reason": "No substitutes registered for this SKU"}

    if criticality == "critical":
        safe = [s for s in substitutes if s.safe_for_critical and s.validated_by == "oem"]
        if not safe:
            return {"substitute": None, "reason": "BLOCKED: No OEM-validated substitute for critical machine",
                    "criticality": criticality}
        best = max(safe, key=lambda s: s.compatibility_score)
    else:
        best = max(substitutes, key=lambda s: s.compatibility_score)

    inv = db.query(Inventory).filter(Inventory.sku == best.substitute_sku).first()
    return {
        "substitute_sku": best.substitute_sku,
        "compatibility_score": best.compatibility_score,
        "validated_by": best.validated_by,
        "safe_for_critical": best.safe_for_critical,
        "in_stock": inv.quantity if inv else 0,
        "criticality": criticality
    }


# ─────────────────────────────────────────────
# LP-06: Workforce-Aware Retrieval ETA
# ─────────────────────────────────────────────

@app.get("/api/inventory/{sku}/retrieval-eta")
def get_retrieval_eta(sku: str, warehouse_id: str = "Warehouse A",
                      user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-06: Returns workforce-aware retrieval ETA."""
    now = datetime.datetime.now()
    day_of_week = now.weekday()  # 0=Mon
    current_time = now.strftime("%H:%M")

    on_shift = db.query(ShiftRoster).filter(
        ShiftRoster.warehouse_id == warehouse_id,
        ShiftRoster.day_of_week == day_of_week,
        ShiftRoster.shift_start <= current_time,
        ShiftRoster.shift_end >= current_time
    ).all()

    if not on_shift:
        return {"eta_minutes": None, "status": "NO_STAFF",
                "message": "No warehouse staff on shift. Earliest availability: next shift at 07:00."}

    authorized = [s for s in on_shift if db.query(WarehouseAccess).filter(
        WarehouseAccess.staff_id == s.staff_id,
        WarehouseAccess.warehouse_id == warehouse_id,
        WarehouseAccess.access_level == "full"
    ).first()]

    base_eta = 12  # Default 12-min walking retrieval
    if not authorized:
        return {"eta_minutes": base_eta + 30, "status": "ACCESS_DELAY",
                "message": "Staff on shift but no full access. +30 min estimated for access request."}

    return {"eta_minutes": base_eta, "status": "AVAILABLE",
            "available_staff_count": len(authorized),
            "message": f"{len(authorized)} authorized staff on shift. Retrieval ~{base_eta} min."}


# ─────────────────────────────────────────────
# LP-08: User Trust Momentum
# ─────────────────────────────────────────────

@app.get("/api/users/{user_id}/trust-profile")
def get_trust_profile(user_id: str, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-08: Return a user's trust score and savings metrics."""
    profile = db.query(UserTrustMetric).filter(UserTrustMetric.user_id == user_id).first()
    if not profile:
        profile = UserTrustMetric(user_id=user_id)
        db.add(profile)
        db.commit()
    return {
        "user_id": profile.user_id,
        "trust_score": profile.trust_score,
        "total_checks": profile.total_checks,
        "followed_recommendations": profile.followed_recommendations,
        "internal_retrievals_successful": profile.internal_retrievals_successful,
        "estimated_cost_saved": round(profile.estimated_cost_saved, 2),
        "estimated_time_saved_minutes": profile.estimated_time_saved_minutes
    }


# ─────────────────────────────────────────────
# LP-09: Item Synonym Normalization
# ─────────────────────────────────────────────

@app.get("/api/items/normalize")
def normalize_item(description: str, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-09: Normalize a raw item description to a canonical SKU."""
    clean = description.lower().strip()
    # Direct synonym match
    match = db.query(ItemSynonym).filter(ItemSynonym.synonym == clean).first()
    if match:
        inv = db.query(Inventory).filter(Inventory.sku == match.canonical_sku).first()
        return {"canonical_sku": match.canonical_sku, "confidence": 1.0, "method": "synonym_match",
                "item_name": inv.name if inv else None}

    # Fuzzy match
    import difflib
    all_synonyms = db.query(ItemSynonym).all()
    synonym_texts = [s.synonym for s in all_synonyms]
    close = difflib.get_close_matches(clean, synonym_texts, n=1, cutoff=0.70)
    if close:
        match = next((s for s in all_synonyms if s.synonym == close[0]), None)
        if match:
            # Auto-learn
            db.add(ItemSynonym(canonical_sku=match.canonical_sku, synonym=clean, source="auto_learned"))
            db.commit()
            return {"canonical_sku": match.canonical_sku, "confidence": 0.80, "method": "fuzzy_match",
                    "matched_synonym": close[0]}

    return {"canonical_sku": None, "confidence": 0.0, "method": "needs_review",
            "message": "Could not normalize. Route to human review."}


# ─────────────────────────────────────────────
# LP-10: Living Risk Score
# ─────────────────────────────────────────────

RISK_ADJUSTMENTS = {
    "delivery_scan_confirmed": -20,
    "po_retroactively_matched": -25,
    "physical_verification_passed": -30,
    "reviewer_confirmed_shadow": +20,
    "verification_missed_deadline": +15,
    "duplicate_vendor_flag": +10
}


class RiskEventRequest(BaseModel):
    event_type: str


@app.post("/api/shadows/{shadow_id}/risk-event")
def update_living_risk(shadow_id: int, body: RiskEventRequest,
                       user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-10: Update living risk score based on a new evidence event."""
    shadow = db.query(ShadowPurchase).filter(ShadowPurchase.id == shadow_id).first()
    if not shadow:
        raise HTTPException(status_code=404, detail="Shadow not found")

    delta = RISK_ADJUSTMENTS.get(body.event_type, 0)
    old_score = shadow.risk_score or 0
    new_score = max(0.0, min(1.0, old_score + delta / 100.0))
    shadow.risk_score = new_score

    db.add(RiskScoreHistory(
        shadow_id=shadow_id,
        score=new_score,
        timestamp=datetime.datetime.now().isoformat(),
        trigger_event=body.event_type
    ))

    if new_score < 0.20:
        shadow.status = "Auto-Resolved"
        _log_event(db, "LP10_AUTO_RESOLVED", str(shadow_id), f"Risk dropped to {new_score:.2f} — auto-resolved")

    db.commit()
    return {"shadow_id": shadow_id, "old_risk": old_score, "new_risk": new_score,
            "delta": delta, "auto_resolved": shadow.status == "Auto-Resolved"}


# ─────────────────────────────────────────────
# LP-11: Predictive Depletion
# ─────────────────────────────────────────────

@app.get("/api/alerts/depletion")
def get_depletion_alerts(horizon: int = 30, user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-11: Return predicted stock-outs within the given horizon (days)."""
    cutoff = (datetime.date.today() + datetime.timedelta(days=horizon)).isoformat()
    alerts = db.query(DepletionAlert).filter(
        DepletionAlert.predicted_need_date <= cutoff,
        DepletionAlert.status == "pending"
    ).all()
    return [{"id": a.id, "sku": a.sku, "predicted_need_date": a.predicted_need_date,
             "confidence": a.confidence, "suggested_order_qty": a.suggested_order_qty} for a in alerts]


@app.post("/api/alerts/depletion/run")
def run_depletion_prediction(user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-11: Run predictive depletion engine across all active SKUs."""
    items = db.query(Inventory).all()
    created = 0
    today = datetime.date.today()

    for item in items:
        logs = db.query(MachineUsageLog).filter(
            MachineUsageLog.part_sku == item.sku
        ).all()
        if len(logs) < 3:
            continue

        total_used = sum(l.quantity_used for l in logs)
        days_span = max(1, (today - datetime.date.fromisoformat(min(l.event_date for l in logs))).days)
        avg_per_day = total_used / days_span

        if avg_per_day <= 0:
            continue

        days_left = item.quantity / avg_per_day
        if days_left <= 30:
            predicted_date = (today + datetime.timedelta(days=int(days_left))).isoformat()
            existing = db.query(DepletionAlert).filter(
                DepletionAlert.sku == item.sku, DepletionAlert.status == "pending"
            ).first()
            if not existing:
                db.add(DepletionAlert(
                    sku=item.sku,
                    predicted_need_date=predicted_date,
                    confidence=min(0.95, len(logs) / 20.0),
                    suggested_order_qty=int(avg_per_day * 45),
                    status="pending",
                    created_at=datetime.datetime.now().isoformat()
                ))
                created += 1

    db.commit()
    return {"status": "done", "alerts_created": created}


# ─────────────────────────────────────────────
# LP-12: Cross-Warehouse Network Mesh
# ─────────────────────────────────────────────

@app.get("/api/inventory/network-search")
def network_inventory_search(sku: str, requesting_location: str = "Warehouse A",
                              user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """LP-12: Search all warehouses for stock, compare transfer vs. buy cost."""
    locations = db.query(InventoryLocation).filter(
        InventoryLocation.sku == sku,
        InventoryLocation.quantity > 0,
        InventoryLocation.confidence_score > 50
    ).all()

    results = []
    for loc in locations:
        if loc.warehouse_id == requesting_location:
            continue
        transfer = db.query(WarehouseTransferCost).filter(
            WarehouseTransferCost.from_warehouse == loc.warehouse_id,
            WarehouseTransferCost.to_warehouse == requesting_location
        ).first()

        inv = db.query(Inventory).filter(Inventory.sku == sku).first()
        external_price = (inv.unit_price * 1.35) if inv else 999.0  # 35% markup for external

        eta = transfer.eta_minutes if transfer else 60
        cost = transfer.cost_per_transfer if transfer else 100.0

        results.append({
            "warehouse": loc.warehouse_id,
            "quantity": loc.quantity,
            "confidence": loc.confidence_score,
            "transfer_eta_minutes": eta,
            "transfer_cost": cost,
            "external_purchase_cost": round(external_price, 2),
            "recommendation": "TRANSFER" if cost < external_price * 0.7 else "COMPARE"
        })

    results.sort(key=lambda x: x["transfer_eta_minutes"])
    return {
        "sku": sku,
        "requesting_location": requesting_location,
        "network_results": results,
        "best_option": results[0] if results else None,
        "total_locations_with_stock": len(results)
    }
