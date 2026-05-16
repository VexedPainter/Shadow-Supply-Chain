"""
AI Module for Shadow Supply Chain Detection v3.0.

1. Multi-Feature Anomaly Detection — Isolation Forest using:
   - Transaction amount
   - Vendor risk score (Low=0, Medium=0.5, High=1)
   - Payment type risk (Invoice=0, Expense=0.5, Corporate Card=1)
   - Day-of-week pattern (weekday=0, weekend=1)

2. Text Classification — Rule-based NLP for item categorization.

3. Data Ingestion Layer — Simulates ERP/financial system extraction.

4. Decision Recommendation Engine — Explainable AI recommendations.

5. Human Feedback Integration — Adjusts confidence from user corrections.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)


class DataIngestionLayer:
    """
    Simulates extraction from structured ERP and financial databases.
    In production: would connect to SAP, Oracle, or similar via APIs/DB queries.
    """

    @staticmethod
    def extract_transaction_features(txn_dict: dict, vendor_info: dict = None) -> dict:
        """
        Extract structured features from raw transaction data.
        Mirrors real ERP data extraction pipeline.
        Produces 10 features matching the README specification exactly.
        """
        # Parse date features
        try:
            date_str = str(txn_dict.get("date", ""))[:10]  # Trim to YYYY-MM-DD
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            is_weekend = 1.0 if dt.weekday() >= 5 else 0.0
        except (ValueError, TypeError):
            is_weekend = 0.0

        # F9: Hour risk — after-hours purchases (requires timestamp HH portion)
        try:
            date_full = str(txn_dict.get("date", ""))
            if " " in date_full:
                hour = int(date_full.split(" ")[1][:2])
            elif txn_dict.get("hour") is not None:
                hour = int(str(txn_dict.get("hour"))[:2])
            else:
                hour = 9  # Default business hours
            hour_risk = 1.0 if (hour < 7 or hour > 20) else 0.0
        except (ValueError, TypeError, IndexError):
            hour_risk = 0.0

        # Payment type risk
        ptype = txn_dict.get("payment_type", "")
        payment_risk = {"Invoice": 0.0, "Expense Claim": 0.5, "Corporate Card": 1.0}.get(ptype, 0.5)

        # Vendor risk
        vendor_risk = 0.5
        vendor_approved = True
        vendor_avg = 0.0
        if vendor_info:
            vendor_risk = {"Low": 0.0, "Medium": 0.5, "High": 1.0}.get(
                vendor_info.get("risk_level", "Medium"), 0.5
            )
            vendor_approved = vendor_info.get("approved", True)
            vendor_avg = float(vendor_info.get("avg_order", 0) or 0)

        # F7: Amount deviation from vendor average
        amount = float(txn_dict.get("amount", 0))
        if vendor_avg > 0:
            amount_deviation = abs(amount - vendor_avg) / vendor_avg
        else:
            amount_deviation = 0.0

        # F8: Department shadow rate (passed from detection context or default)
        dept_risk_score = float(txn_dict.get("dept_risk_score", 0.5))

        # F10: Recurring vendor pattern (same vendor purchased 3+ times — passed in)
        is_recurring = float(txn_dict.get("is_recurring", 0))

        return {
            "amount": amount,
            "payment_risk": payment_risk,
            "vendor_risk": vendor_risk,
            "is_weekend": is_weekend,
            "vendor_approved": vendor_approved,
            "has_card_holder": txn_dict.get("card_holder", "System") != "System",
            "amount_deviation": round(amount_deviation, 3),
            "dept_risk_score": dept_risk_score,
            "hour_risk": hour_risk,
            "is_recurring": is_recurring,
        }


class ShadowAI:
    def __init__(self):
        self.anomaly_detector = IsolationForest(
            contamination=0.2, random_state=42, n_estimators=150
        )
        self._fitted = False
        self._contamination = 0.2
        self.ingestion = DataIngestionLayer()
        # Feedback-adjusted confidence offsets (category -> adjustment)
        self._feedback_adjustments: dict[str, float] = {}
        self._feedback_count = 0
        # Preserved for retraining — stores the original training corpus
        self._last_training_set: list[dict] = []

    def _feature_vector(self, features: dict) -> list:
        """
        10-feature vector for Isolation Forest.
        Matches README specification exactly.

        F1  amount            – transaction dollar value (continuous)
        F2  payment_risk      – 0=Invoice, 0.5=Expense Claim, 1.0=Corp Card
        F3  vendor_risk       – 0=Low, 0.5=Medium, 1.0=High
        F4  is_weekend        – 1 if Sat/Sun, else 0
        F5  vendor_approved   – 0=approved, 1=unapproved (risk inversion)
        F6  has_card_holder   – 1 if named employee, 0 if system/automated
        F7  amount_deviation  – deviation from vendor's historical avg (normalized)
        F8  dept_risk_score   – department's shadow purchase rate (0–1)
        F9  hour_risk         – 1 if purchase outside 07:00–20:00, else 0
        F10 is_recurring      – 1 if same vendor purchased 3+ times this month
        """
        return [
            float(features.get("amount", 0)),                          # F1
            float(features.get("payment_risk", 0.5)),                  # F2
            float(features.get("vendor_risk", 0.5)),                   # F3
            float(features.get("is_weekend", 0)),                      # F4
            0.0 if features.get("vendor_approved", True) else 1.0,    # F5: unapproved = higher risk
            1.0 if features.get("has_card_holder", False) else 0.0,   # F6
            float(features.get("amount_deviation", 0)),                # F7
            float(features.get("dept_risk_score", 0.5)),               # F8
            float(features.get("hour_risk", 0)),                       # F9
            float(features.get("is_recurring", 0)),                    # F10
        ]

    def fit_anomaly_detector(self, feature_sets: list[dict]):
        """Train Isolation Forest on 10-dimensional transaction feature vectors."""
        if len(feature_sets) < 5:
            return
        X = np.array([self._feature_vector(f) for f in feature_sets])
        self.anomaly_detector.fit(X)
        self._fitted = True
        # Preserve training corpus so retrain_from_feedback can extend it
        self._last_training_set = list(feature_sets)

    def get_anomaly_score(self, features: dict) -> float:
        """Return risk score 0-1. Higher = more anomalous."""
        if not self._fitted:
            # Fallback heuristic (model not yet trained)
            base = 0.3
            if features.get("payment_risk", 0) > 0.5:
                base += 0.15
            if features.get("vendor_risk", 0) > 0.5:
                base += 0.2
            if features.get("amount", 0) > 2000:
                base += 0.15
            if not features.get("vendor_approved", True):
                base += 0.1
            return min(1.0, round(base, 3))

        X = np.array([self._feature_vector(features)])
        score = self.anomaly_detector.decision_function(X)[0]
        # Normalize: decision_function gives negative for anomalies
        normalized = max(0.0, min(1.0, 0.5 - score * 0.8))

        # Apply feedback adjustments
        adj = self._feedback_adjustments.get("_global", 0.0)
        normalized = max(0.0, min(1.0, normalized + adj))

        return round(normalized, 3)

    def get_anomaly_breakdown(self, features: dict) -> list[str]:
        """Return human-readable anomaly factors (XAI Layer)."""
        factors = []
        # Financial Factors
        if features.get("amount", 0) > 3000:
            factors.append(f"High transaction amount (${features['amount']:,.0f}) — exceeds 3x typical deviation")
        elif features.get("amount", 0) > 1500:
            factors.append(f"Above-average amount (${features['amount']:,.0f})")
        
        # Process Factors
        if features.get("payment_risk", 0) >= 1.0:
            factors.append("Corporate card purchase — bypasses internal procurement controls")
        elif features.get("payment_risk", 0) >= 0.5:
            factors.append("Expense claim — high potential for manual entry errors")
        
        # Vendor Factors
        if features.get("vendor_risk", 0) >= 1.0:
            factors.append("High-risk vendor category — requires periodic audit")
        elif features.get("vendor_risk", 0) >= 0.5:
            factors.append("Medium-risk vendor category")
        
        if not features.get("vendor_approved", True):
            factors.append("Unapproved/Unknown Vendor — no established Master Service Agreement (MSA)")
        
        # Timing Factors
        if features.get("is_weekend", 0):
            factors.append("Weekend purchase — unusual timing for standard business operations")
            
        return factors

    # ─── Financial Impact Engine ──────────────────────────
    def calculate_risk_impact(self, amount: float, anomaly_score: float, vendor_risk_level: str) -> dict:
        """
        Calculate estimated financial loss and impact category.
        Formula: impact = amount * anomaly_score * vendor_multiplier
        """
        multiplier = {"Low": 1.0, "Medium": 1.5, "High": 2.5}.get(vendor_risk_level, 1.5)
        impact_score = amount * anomaly_score * multiplier
        
        # Categorize
        if impact_score > 5000:
            category = "Critical"
        elif impact_score > 1500:
            category = "High"
        elif impact_score > 500:
            category = "Medium"
        else:
            category = "Low"
            
        return {
            "estimated_loss": round(impact_score, 2),
            "category": category,
            "multiplier": multiplier
        }

    # ─── System Confidence Engine ─────────────────────────
    def calculate_confidence(self, features: dict, txn_data: dict) -> float:
        """
        Compute reliability estimation for AI prediction (0-1).
        Weighted by data quality and pattern consistency.
        """
        score = 1.0
        
        # 1. Data Completeness (30% weight)
        if not features.get("vendor_approved", True): score -= 0.15
        if not txn_data.get("description") or len(txn_data["description"]) < 5: score -= 0.1
        if not txn_data.get("department"): score -= 0.05
        
        # 2. Model Consistency (40% weight)
        # Simulate consistency check (in real world, compare with past predictions)
        if features.get("amount", 0) > 10000: score -= 0.1 # Outliers reduce confidence
        
        # 3. Pattern Match (30% weight)
        # Weekend purchases on expense claims are highly predictable (high confidence)
        if features.get("is_weekend") and features.get("payment_risk") >= 0.5:
            score += 0.05 
            
        return max(0.2, min(0.98, round(score, 2)))

    # ─── Action Recommendation Engine ─────────────────────
    def generate_action_recommendation(self, risk_score: float, confidence: float, features: dict) -> str:
        """Rule-based decision support logic."""
        if risk_score > 0.8:
            return "AUDIT: Immediate stop-payment and internal internal review required."
        if not features.get("vendor_approved", True):
            return "VERIFY VENDOR: Contact Accounts Payable to validate vendor credentialing."
        if risk_score > 0.5 and confidence > 0.7:
            return "INVESTIGATE: Pattern suggests recurring shadow behavior. Review department spend."
        if risk_score > 0.4:
            return "CONVERT TO PO: Integrate into existing procurement pipeline to capture discounts."
        
        return "MONITOR: Flagged as variance, continue tracking for behavioral trends."

    def get_data_quality(self, txn_data: dict) -> str:
        """Detect Reliability of inputs."""
        missing = []
        if not txn_data.get("vendor"): missing.append("Vendor")
        if not txn_data.get("description") or "txn" in txn_data["description"].lower(): missing.append("Clear Description")
        
        if not missing: return "Good"
        if len(missing) >= 2: return "Low"
        return "Vague"

    def normalize_and_classify_item(self, description: str) -> dict:
        """Module 3: Semantic Normalization and Classification Engine."""
        desc = description.lower()
        
        # 1. Semantic Normalization (Synonym Dictionary)
        synonyms = {
            "bearing": ["brg", "ball bearing", "roller bearing", "tapered bearing"],
            "motor": ["mtr", "elec motor", "drive motor"],
            "pump": ["pmp", "water pump", "hydraulic pump"],
            "valve": ["vlv", "gate valve", "ball valve", "check valve"],
            "filter": ["fltr", "air filter", "oil filter"],
            "sensor": ["snr", "transducer", "probe", "detector"]
        }
        
        canonical_name = description
        norm_score = 0.5
        for canon, variations in synonyms.items():
            if canon in desc or any(v in desc for v in variations):
                canonical_name = canon.title()
                norm_score = 0.95
                break

        # 2. Category Mapping
        categories = {
            "Pumps & Motors":     ["pump", "motor", "compressor", "conveyor", "starter", "alternator"],
            "Electrical & PLC":   ["plc", "control board", "electrical", "cable", "wire", "module", "thermocouple", "sensor"],
            "Fasteners":          ["bolt", "screw", "nut", "fastener", "rivet", "hex"],
            "Hydraulics":         ["hydraulic", "hose", "fitting", "valve", "seal", "o-ring", "gasket", "pressure"],
            "Safety Equipment":   ["safety", "goggle", "helmet", "glove", "vest", "hard hat", "fire extinguisher", "first aid"],
            "HVAC":               ["hvac", "filter", "air conditioning", "heating"],
            "Welding":            ["weld", "electrode", "rod", "flux"],
            "Tools":              ["wrench", "tool", "drill", "saw", "hammer", "caliper"],
            "Cleaning & Chemicals": ["clean", "wd-40", "lubricant", "solvent", "supply", "degreaser", "paint", "tape"],
            "Raw Materials":      ["steel", "plate", "sheet", "pipe", "pvc", "bracket"],
            "Bearings":           ["bearing", "brg"],
            "Power Transmission": ["belt", "tensioner", "chain", "sprocket", "v-belt"],
        }
        
        category = "General / Uncategorized"
        cat_confidence = 0.3
        for cat, keywords in categories.items():
            if any(kw in desc for kw in keywords):
                category = cat
                cat_confidence = 0.9
                break

        # 3. SKU Mapping Guess
        sku_prefix = "".join([word[0].upper() for word in category.split() if word.isalpha()])
        sku_guess = f"{sku_prefix}-{random.randint(1000, 9999)}" if category != "General / Uncategorized" else "UNKNOWN"
        
        overall_confidence = (norm_score + cat_confidence) / 2.0
        
        return {
            "canonical_name": canonical_name,
            "category": category,
            "sku_guess": sku_guess,
            "confidence": round(overall_confidence, 2),
            "needs_human_review": overall_confidence < 0.7
        }

    def classify_item(self, description: str) -> str:
        """Legacy compatibility wrapper."""
        return self.normalize_and_classify_item(description)["category"]

    # ─── Decision Recommendation Engine ────────────────────
    def generate_recommendations(self, shadows: list, vendors: dict, transactions: dict) -> list[dict]:
        """
        Generate explainable decision recommendations.
        Returns list of {type, priority, title, explanation, action, target_id}
        """
        recommendations = []

        for s in shadows:
            if s.status != "Pending":
                continue

            txn = transactions.get(s.transaction_id)
            if not txn:
                continue

            risk = s.risk_score or 0
            rec = {
                "target_id": s.id,
                "transaction_id": s.transaction_id,
            }

            # High-value shadow → immediate PO conversion
            if txn.amount > 1000 and risk > 0.5:
                rec.update({
                    "type": "convert_to_po",
                    "priority": "high",
                    "title": f"Convert ${txn.amount:,.0f} shadow purchase to PO",
                    "explanation": (
                        f"Transaction {txn.id} from {txn.vendor} for ${txn.amount:,.2f} "
                        f"has a risk score of {risk:.0%}. High-value untracked purchases "
                        f"increase audit exposure. Converting to a formal PO ensures "
                        f"compliance and inventory tracking."
                    ),
                    "action": "resolve",
                })
            elif risk > 0.6:
                rec.update({
                    "type": "investigate",
                    "priority": "high",
                    "title": f"Investigate high-risk transaction from {txn.vendor}",
                    "explanation": (
                        f"AI risk score is {risk:.0%}. Factors: {s.reason}. "
                        f"This vendor may be circumventing procurement controls."
                    ),
                    "action": "review",
                })
            else:
                rec.update({
                    "type": "convert_to_po",
                    "priority": "medium",
                    "title": f"Review ${txn.amount:,.0f} purchase from {txn.vendor}",
                    "explanation": (
                        f"No matching PO found for {txn.description}. "
                        f"Category: {s.item_category or 'Unknown'}. "
                        f"Consider converting to formal procurement record."
                    ),
                    "action": "resolve",
                })

            recommendations.append(rec)

        # Vendor-level recommendations
        for name, vendor in vendors.items():
            shadow_count = sum(
                1 for s in shadows
                if transactions.get(s.transaction_id) and
                transactions[s.transaction_id].vendor == name and
                s.status == "Pending"
            )
            if shadow_count >= 3:
                recommendations.append({
                    "type": "vendor_risk",
                    "priority": "critical",
                    "target_id": vendor.id,
                    "vendor_name": name,
                    "transaction_id": None,
                    "title": f"Vendor '{name}' has {shadow_count} unresolved shadows",
                    "explanation": (
                        f"Vendor '{name}' (Risk: {vendor.risk_level}, "
                        f"Approved: {'Yes' if vendor.approved else 'No'}) "
                        f"has {shadow_count} pending shadow purchases. "
                        f"Consider formal vendor review or adding to approved list."
                    ),
                    "action": "vendor_review",
                })

        # Sort: critical > high > medium
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 9))

        return recommendations[:15]  # Cap at 15

    # ─── Human Feedback Integration ────────────────────────
    def apply_feedback(self, feedback_type: str, original_risk: float,
                       corrected_risk: float = None, category: str = None):
        """Adjust model confidence based on human feedback."""
        self._feedback_count += 1
        
        # Determine movement
        if feedback_type == "incorrect" and corrected_risk is not None:
            # Shift the base risk score towards the human correction
            # delta = (human - ai) * learning_rate
            delta = (corrected_risk - original_risk) * 0.15 
            self._feedback_adjustments["_global"] = self._feedback_adjustments.get("_global", 0.0) + delta
        
        elif feedback_type == "recategorize" and category:
            # If human consistently recategorizes, we could adjust category weights (simulated)
            self._feedback_adjustments[f"cat_{category}"] = self._feedback_adjustments.get(f"cat_{category}", 0.0) + 0.05

        return {
            "feedback_applied": True,
            "total_feedback": self._feedback_count,
            "model_adjustment": round(self._feedback_adjustments.get("_global", 0.0), 4),
            "status": "AI Logic Recalibrated"
        }

    def retrain_from_feedback(self, confirmed_shadows: list, false_positives: list) -> dict:
        """
        Retrain Isolation Forest using feedback-corrected dataset.
        Call this on a schedule (daily) or after every 10 feedback submissions.

        confirmed_shadows: list of feature dicts from reviewer-confirmed shadow purchases
        false_positives:   list of feature dicts from reviewer-confirmed false positives

        Strategy:
        - Oversample false positives to teach model what 'normal' looks like
        - Tune contamination parameter based on confirmed shadow rate
        """
        if not confirmed_shadows and not false_positives:
            return {"retrained": False, "reason": "No feedback data provided"}

        # Compute new contamination estimate from confirmed feedback
        total_feedback = len(confirmed_shadows) + len(false_positives)
        confirmed_rate = len(confirmed_shadows) / total_feedback if total_feedback > 0 else 0.2
        new_contamination = max(0.05, min(0.4, confirmed_rate))

        # Rebuild training corpus: original + oversampled false positives
        all_features = list(self._last_training_set or [])
        # Oversample false positives 3× — teaches the model what 'normal' looks like
        all_features += false_positives * 3

        if len(all_features) < 5:
            return {"retrained": False, "reason": "Insufficient training samples after augmentation"}

        # Retrain with adjusted contamination
        self.anomaly_detector = IsolationForest(
            contamination=new_contamination,
            random_state=42,
            n_estimators=150
        )
        X = np.array([self._feature_vector(f) for f in all_features])
        self.anomaly_detector.fit(X)
        self._fitted = True
        self._contamination = new_contamination
        self._last_training_set = all_features

        logger.info(
            f"[ShadowAI] Retrained: contamination={new_contamination:.3f}, "
            f"samples={len(all_features)}, confirmed={len(confirmed_shadows)}, fp={len(false_positives)}"
        )

        return {
            "retrained": True,
            "new_contamination": round(new_contamination, 4),
            "training_samples": len(all_features),
            "confirmed_shadows_used": len(confirmed_shadows),
            "false_positives_used": len(false_positives),
        }


    def get_decision_explanation(self, features: dict, risk_score: float, category: str) -> dict:
        """Generate full explainable AI output."""
        factors = self.get_anomaly_breakdown(features)
        severity = "critical" if risk_score > 0.7 else "high" if risk_score > 0.5 else "medium" if risk_score > 0.3 else "low"

        return {
            "risk_score": risk_score,
            "severity": severity,
            "category": category,
            "factors": factors,
            "confidence": round(0.7 + (self._feedback_count * 0.01), 2) if self._feedback_count < 30 else 0.95,
            "model_version": "IsolationForest-v3",
            "feedback_adjustments_applied": self._feedback_count,
            "recommendation": (
                "Immediate PO conversion recommended" if risk_score > 0.6
                else "Review and categorize" if risk_score > 0.3
                else "Low risk — monitor only"
            ),
        }


# Singleton
shadow_ai = ShadowAI()


# =============================================================================
# F6: NLP Contract Compliance Checker
# =============================================================================

async def check_contract_compliance(txn: dict, contract_text: str) -> dict:
    """
    F6: Use Groq LLM to check whether a transaction violates a vendor's
    contract / MSA terms.

    Args:
        txn:           dict with keys: vendor, amount, date, payment_type, category
        contract_text: raw contract text (first 2000 chars used to fit context)

    Returns:
        {compliant: bool, violations: [str], severity: "low|medium|high"}

    Gracefully falls back to {compliant: True} if Groq is unavailable.
    """
    if not contract_text or not contract_text.strip():
        return {
            "compliant":  True,
            "violations": [],
            "severity":   "low",
            "note":       "No active contract on file for this vendor",
        }

    prompt = f"""You are a procurement compliance checker.

CONTRACT TERMS (first 2000 chars):
{contract_text[:2000]}

TRANSACTION TO CHECK:
- Vendor:       {txn.get('vendor', '')}
- Amount:       ${txn.get('amount', 0):,.2f}
- Category:     {txn.get('category', 'Unknown')}
- Date:         {txn.get('date', '')}
- Payment type: {txn.get('payment_type', '')}

Does this transaction violate any contract terms?
Reply with valid JSON ONLY — no extra text, no markdown fences:
{{"compliant": true, "violations": [], "severity": "low"}}"""

    try:
        # Lazy import to avoid circular dependency with ai_copilot.py
        from ai_copilot import _init_groq
        client = _init_groq()
        if not client:
            return {
                "compliant":  True,
                "violations": [],
                "severity":   "low",
                "note":       "Groq not configured — compliance check skipped",
            }

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.1,   # Low temperature for deterministic JSON output
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if model adds them anyway
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        # Ensure required keys exist
        return {
            "compliant":  bool(result.get("compliant", True)),
            "violations": list(result.get("violations", [])),
            "severity":   str(result.get("severity", "low")),
        }
    except json.JSONDecodeError as e:
        logger.warning(f"[F6] Contract compliance JSON parse error: {e} | raw={raw[:200]}")
        return {"compliant": True, "violations": [], "severity": "low",
                "error": f"JSON parse error: {e}"}
    except Exception as e:
        logger.warning(f"[F6] Contract compliance check failed: {e}")
        return {"compliant": True, "violations": [], "severity": "low",
                "error": str(e)}
