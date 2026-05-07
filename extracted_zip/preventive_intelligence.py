"""
Preventive Intelligence Layer — ShadowSync-v3 Extension
--------------------------------------------------------
Modules:
  1. Inventory Confidence Engine
  2. Retrieval Time Estimation
  3. Emergency Mode Decision Engine
  4. Smart Part Matching (alternative suggestions)

This module runs BEFORE shadow detection.
If user proceeds to purchase despite recommendation,
the existing detection system captures it.
"""

import datetime
import math
import random
from typing import Optional


# ─── CONFIDENCE THRESHOLDS ────────────────────────────────
CONFIDENCE_HIGH_THRESHOLD = 70      # >= 70% → trusted
CONFIDENCE_MED_THRESHOLD  = 40      # 40-69% → caution
RETRIEVAL_TIME_LIMIT_MIN  = 30      # <= 30 min → acceptable


# ─── LOCATION RETRIEVAL BASE TIMES (minutes) ─────────────
LOCATION_BASE_TIMES = {
    "Warehouse A": 8,
    "Warehouse B": 12,
    "Warehouse C": 20,
    "Storage Room 1": 5,
    "Storage Room 2": 7,
    "Maintenance Bay": 3,
    "Cold Storage": 15,
    "Remote Storage": 45,
    "Off-Site": 60,
}


def _hours_since(timestamp_str: Optional[str]) -> float:
    """Return hours since a given ISO timestamp string. Returns 999 if unknown."""
    if not timestamp_str or timestamp_str in ("N/A", "None", ""):
        return 999
    try:
        # Handle various formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.datetime.strptime(timestamp_str, fmt)
                delta = datetime.datetime.now() - dt
                return delta.total_seconds() / 3600
            except ValueError:
                continue
        return 999
    except Exception:
        return 999


# ─── SECTION 1: INVENTORY CONFIDENCE ENGINE ──────────────

def compute_inventory_confidence(item, db) -> dict:
    """
    Compute confidence score (0-100) for an inventory item.

    confidence_score = f(
        last_update_time,      # recency — 35% weight
        frequency_of_changes,  # stability — 25% weight
        mismatch_history,      # accuracy — 25% weight
        verification_status    # trust marker — 15% weight
    )

    Returns:
        {
            "item_id": str,
            "item_name": str,
            "confidence_score": float (0-100),
            "confidence_label": str ("High" | "Medium" | "Low"),
            "confidence_color": str (CSS color),
            "last_verified": str,
            "breakdown": dict,
        }
    """
    # ── Module 4: New Confidence Formula ──────────────────────
    # 1. Fresh verification: +30
    hours_old = _hours_since(getattr(item, 'last_updated', None))
    verification_score = 0
    if hours_old < 24:
        verification_score = 30
    elif hours_old < 72:
        verification_score = 20
    elif hours_old < 168:
        verification_score = 10

    # Time decay penalty (decays past 1 week)
    if hours_old > 168:
        verification_score = max(-20, -int((hours_old - 168) / 24))

    # 2. Repeated scan consistency: +20
    quantity = getattr(item, 'quantity', 0)
    reorder = getattr(item, 'reorder_level', 0)
    stock_ratio = quantity / max(reorder, 1)
    scan_score = 20 if stock_ratio > 1.5 else (10 if stock_ratio > 0.5 else 0)

    # 3. Low mismatch history: +20
    try:
        from database import InventoryConfidence
        conf_record = db.query(InventoryConfidence).filter(
            InventoryConfidence.item_id == str(item.id)
        ).first()
        mismatch_count = conf_record.mismatch_count if conf_record else 0
        v_status = conf_record.verification_status if conf_record else "unverified"
    except Exception:
        mismatch_count = 0
        v_status = "unverified"

    if mismatch_count == 0:
        mismatch_score = 20
    elif mismatch_count == 1:
        mismatch_score = 10
    else:
        mismatch_score = -10 # unresolved mismatch penalty

    # 4. Verified storage location: +15
    location = getattr(item, 'location', '')
    location_score = 15 if location and location != 'Unknown' else 0

    # 5. Trusted source of update: +15
    source_score = 15 if v_status == "verified" else (5 if v_status == "partial" else 0)

    confidence_score = max(0, min(100, verification_score + scan_score + mismatch_score + location_score + source_score))

    # ── Labels & Colors ───────────────────────────────────
    if confidence_score >= CONFIDENCE_HIGH_THRESHOLD:
        confidence_label = "High"
        confidence_color = "#22c55e"   # green
    elif confidence_score >= CONFIDENCE_MED_THRESHOLD:
        confidence_label = "Medium"
        confidence_color = "#f59e0b"   # amber
    else:
        confidence_label = "Low"
        confidence_color = "#ef4444"   # red

    last_verified = getattr(item, 'last_updated', None) or "Unknown"

    return {
        "item_id": str(item.id),
        "item_name": item.name,
        "confidence_score": confidence_score,
        "confidence_label": confidence_label,
        "confidence_color": confidence_color,
        "last_verified": last_verified,
        "hours_since_update": round(hours_old, 1),
        "breakdown": {
            "recency": round(recency_score * 0.35, 1),
            "stability": round(frequency_score * 0.25, 1),
            "accuracy": round(mismatch_score * 0.25, 1),
            "verification": round(verification_score * 0.15, 1),
        }
    }


# ─── SECTION 2: RETRIEVAL TIME ESTIMATION ────────────────

def estimate_retrieval_time(item, db=None) -> dict:
    """
    Estimate how quickly an inventory item can be accessed.

    retrieval_time = base_time(location) + historical_variance

    Returns:
        {
            "item_id": str,
            "warehouse_location": str,
            "estimated_minutes": int,
            "time_label": str ("Fast" | "Moderate" | "Slow"),
            "time_color": str,
            "distance_km": float,
        }
    """
    location = getattr(item, 'location', None) or "Warehouse A"

    # ── Module 6: Retrieval ETA Calculation ────────────────
    # 1. Base Time (Distance)
    base_time = LOCATION_BASE_TIMES.get(location, 20)

    # 2. Equipment Type (heavy/light)
    category = getattr(item, 'category', '').lower()
    heavy_categories = ['pumps & motors', 'raw materials', 'power transmission', 'hvac']
    is_heavy = any(c in category for c in heavy_categories)
    equip_modifier = 15 if is_heavy else 0

    # 3. Verification Status Penalty (Search time)
    try:
        from database import InventoryConfidence
        conf_record = db.query(InventoryConfidence).filter(
            InventoryConfidence.item_id == str(item.id)
        ).first()
        v_status = conf_record.verification_status if conf_record else "unverified"
    except Exception:
        v_status = "unverified"
    
    verification_penalty = 0 if v_status == "verified" else (10 if v_status == "partial" else 25)

    # 4. Historical variance
    historical_adjustment = 0
    if db:
        try:
            from database import RetrievalLog
            logs = db.query(RetrievalLog).filter(
                RetrievalLog.item_id == str(item.id)
            ).order_by(RetrievalLog.id.desc()).limit(5).all()
            if logs:
                avg_actual = sum(l.retrieval_time_minutes for l in logs) / len(logs)
                historical_adjustment = round(avg_actual - base_time, 1)
        except Exception:
            pass

    # Item quantity affects access time
    quantity = getattr(item, 'quantity', 0)
    if quantity == 0:
        # Item not in stock — infinite retrieval
        return {
            "item_id": str(item.id),
            "warehouse_location": location,
            "estimated_minutes": None,
            "time_label": "Not Available",
            "time_color": "#ef4444",
            "in_stock": False,
            "distance_km": round(base_time * 0.4, 1),
        }

    # Small randomness to simulate realistic variation (±20%)
    variance_factor = 1.0 + (random.uniform(-0.15, 0.25))
    final_time = max(2, round((base_time + equip_modifier + verification_penalty + historical_adjustment) * variance_factor))

    if final_time <= 10:
        time_label, time_color = "Fast", "#22c55e"
    elif final_time <= 25:
        time_label, time_color = "Moderate", "#f59e0b"
    else:
        time_label, time_color = "Slow", "#ef4444"

    return {
        "item_id": str(item.id),
        "warehouse_location": location,
        "estimated_minutes": final_time,
        "time_label": time_label,
        "time_color": time_color,
        "in_stock": True,
        "distance_km": round(base_time * 0.4, 1),
    }


# ─── SECTION 3: EMERGENCY MODE DECISION ENGINE ───────────

def make_emergency_decision(item, db, part_name: str = None, machine_id: str = None) -> dict:
    """
    Core decision logic for emergency procurement scenarios.

    Decision Logic:
        IF item exists AND confidence >= 70 AND retrieval_time <= 30:
            recommend "Use internal stock"
        ELIF item exists AND confidence >= 40:
            recommend "Verify manually before purchase"
        ELSE:
            recommend "Proceed with procurement"

    Returns complete decision package including alternatives.
    """
    confidence_data = compute_inventory_confidence(item, db)
    retrieval_data  = estimate_retrieval_time(item, db)

    confidence_score = confidence_data["confidence_score"]
    retrieval_minutes = retrieval_data.get("estimated_minutes")
    in_stock = retrieval_data["in_stock"]

    # ── Module 5: 3-Tier Decision Logic ────────────────────────────────────
    action_required = ""

    # TIER 1: HIGH CONFIDENCE, FAST RETRIEVAL -> Strictly use internal stock
    if in_stock and confidence_score >= CONFIDENCE_HIGH_THRESHOLD and retrieval_minutes is not None and retrieval_minutes <= RETRIEVAL_TIME_LIMIT_MIN:
        decision = "Use Internal Stock"
        decision_color = "#22c55e"
        decision_icon = "✅"
        action_required = "Issue internal retrieval ticket."
        reason = (
            f"Item available at {retrieval_data['warehouse_location']} with "
            f"{confidence_score:.0f}% data confidence. "
            f"Estimated access in {retrieval_minutes} minutes — well within emergency threshold."
        )
        severity = "safe"

    # TIER 2: MEDIUM CONFIDENCE OR SLOW RETRIEVAL -> Require human verification
    elif in_stock and (confidence_score >= CONFIDENCE_MED_THRESHOLD or (retrieval_minutes and retrieval_minutes > RETRIEVAL_TIME_LIMIT_MIN)):
        decision = "Verify Manually First"
        decision_color = "#f59e0b"
        decision_icon = "⚠️"
        action_required = "Generate physical verification task."
        time_str = f"{retrieval_minutes} min" if retrieval_minutes else "unknown time"
        reason = (
            f"Item appears to be in stock at {retrieval_data['warehouse_location']}, "
            f"but confidence is {confidence_score:.0f}% or retrieval is slow. "
            f"Recommend physical verification before proceeding. "
            f"If confirmed, retrieval ~{time_str}."
        )
        severity = "caution"

    # TIER 3: LOW CONFIDENCE OR OUT OF STOCK -> Approve external purchase
    else:
        decision = "Proceed with Procurement"
        decision_color = "#ef4444"
        decision_icon = "🔴"
        action_required = "Create PO draft."
        if not in_stock:
            reason = (
                f"Item is not currently in stock. "
                f"Emergency procurement is justified. "
            )
        else:
            reason = (
                f"Inventory data confidence is very low ({confidence_score:.0f}%). "
                f"The system cannot reliably verify stock availability. "
                f"Emergency procurement is justified."
            )
        severity = "critical"

    # ── Find Alternatives ─────────────────────────────────
    alternatives = find_smart_alternatives(part_name or item.name, db, exclude_id=str(item.id), machine_id=machine_id)

    return {
        "item_id": str(item.id),
        "item_name": item.name,
        "item_sku": getattr(item, 'sku', ''),
        "quantity_available": getattr(item, 'quantity', 0),
        "unit_price": getattr(item, 'unit_price', 0),
        "decision": decision,
        "decision_color": decision_color,
        "decision_icon": decision_icon,
        "reason": reason,
        "severity": severity,
        "confidence": confidence_data,
        "retrieval": retrieval_data,
        "action_required": action_required,
        "alternatives": alternatives[:3],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ─── SECTION 4: SMART PART MATCHING ─────────────────────

def find_smart_alternatives(part_name: str, db, exclude_id: str = None, top_n: int = 3, machine_id: str = None) -> list:
    """
    Suggest alternatives when exact part is not found or confidence is low.

    Uses token-overlap similarity: tokenize query + inventory names,
    score by matching tokens, return top-N scored items.
    Enforces LP-04 Safety checks if machine_id is provided.
    """
    from database import Inventory, PartsCompatibility, MachineCriticality

    try:
        all_items = db.query(Inventory).filter(
            Inventory.quantity > 0  # Only in-stock alternatives
        ).all()
    except Exception:
        return []

    # Check criticality
    is_critical = False
    if machine_id:
        crit_record = db.query(MachineCriticality).filter(MachineCriticality.machine_id == machine_id).first()
        if crit_record and crit_record.criticality_level == 'critical':
            is_critical = True

    query_tokens = set(_tokenize(part_name))
    if not query_tokens:
        return []

    scored = []
    for item in all_items:
        if exclude_id and str(item.id) == exclude_id:
            continue
            
        # LP-04 Safety Check
        if is_critical and exclude_id:
            # Need to find original item sku
            orig_item = db.query(Inventory).filter(Inventory.id == exclude_id).first()
            if orig_item:
                compat = db.query(PartsCompatibility).filter(
                    PartsCompatibility.primary_sku == orig_item.sku,
                    PartsCompatibility.substitute_sku == item.sku
                ).first()
                if not compat or not compat.safe_for_critical or compat.validated_by != 'oem':
                    continue # Block unsafe substitute

        # Score by name + category token overlap
        name_tokens = set(_tokenize(item.name))
        cat_tokens  = set(_tokenize(getattr(item, 'category', '') or ''))
        all_item_tokens = name_tokens | cat_tokens

        if not all_item_tokens:
            continue

        # Jaccard similarity: intersection / union
        intersection = len(query_tokens & all_item_tokens)
        union = len(query_tokens | all_item_tokens)
        score = intersection / union if union > 0 else 0

        if score > 0:
            scored.append({
                "item_id": str(item.id),
                "item_name": item.name,
                "sku": getattr(item, 'sku', ''),
                "category": getattr(item, 'category', ''),
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "location": getattr(item, 'location', ''),
                "similarity_score": round(score * 100, 1),
                "compatibility_note": _infer_compatibility(part_name, item.name),
            })

    # Sort by similarity descending
    scored.sort(key=lambda x: x['similarity_score'], reverse=True)
    return scored[:top_n]


def _tokenize(text: str) -> list:
    """Simple tokenizer: lowercase, split on spaces/hyphens/underscores."""
    if not text:
        return []
    import re
    text = text.lower()
    tokens = re.split(r'[\s\-_/,\.]+', text)
    # Remove short tokens and common stop words
    stop_words = {'and', 'or', 'for', 'the', 'a', 'an', 'with', 'in', 'on', 'at', 'of', 'to'}
    return [t for t in tokens if len(t) > 1 and t not in stop_words]


def _infer_compatibility(query: str, item_name: str) -> str:
    """Generate a human-readable compatibility note."""
    q_tokens = set(_tokenize(query))
    i_tokens = set(_tokenize(item_name))
    shared = q_tokens & i_tokens

    if len(shared) >= 2:
        return f"Shares components: {', '.join(list(shared)[:3])}"
    elif shared:
        return f"Partial match on: {list(shared)[0]}"
    else:
        return "May be compatible — verify specs"


def normalize_item_description(raw_text: str, db) -> dict:
    """
    LP-09: Normalization engine.
    Finds the canonical SKU for an item description.
    """
    from database import ItemSynonyms
    import difflib
    
    clean = raw_text.lower().strip()
    
    # Step 1: Direct synonym lookup
    match = db.query(ItemSynonyms).filter(ItemSynonyms.synonym == clean).first()
    if match:
        return {"canonical_sku": match.canonical_sku, "confidence": 1.0, "method": "synonym_match"}
        
    # Step 2: Fuzzy matching against all known synonyms
    all_synonyms = db.query(ItemSynonyms).all()
    synonym_strings = [s.synonym for s in all_synonyms]
    if synonym_strings:
        closest = difflib.get_close_matches(clean, synonym_strings, n=1, cutoff=0.75)
        if closest:
            best_synonym = closest[0]
            match = db.query(ItemSynonyms).filter(ItemSynonyms.synonym == best_synonym).first()
            if match:
                # Auto-learn: add this as a new synonym for future use
                new_synonym = ItemSynonyms(canonical_sku=match.canonical_sku, synonym=clean, source='auto_learned')
                db.add(new_synonym)
                db.commit()
                # Compute confidence based on SequenceMatcher
                ratio = difflib.SequenceMatcher(None, clean, best_synonym).ratio()
                return {"canonical_sku": match.canonical_sku, "confidence": ratio, "method": "fuzzy_match"}
                
    return {"canonical_sku": None, "confidence": 0, "method": "needs_review"}


# ─── BULK CONFIDENCE REPORT ───────────────────────────────

def get_all_confidence_scores(db) -> list:
    """Return confidence scores for all inventory items."""
    from database import Inventory

    try:
        items = db.query(Inventory).order_by(Inventory.category).all()
        results = []
        for item in items:
            c = compute_inventory_confidence(item, db)
            r = estimate_retrieval_time(item, db)
            results.append({**c, "retrieval": r})
        return results
    except Exception:
        return []
