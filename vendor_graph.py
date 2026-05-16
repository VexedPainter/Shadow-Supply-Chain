"""
Vendor Ring Detection Engine v1.0
====================================
Builds a bipartite graph of Vendor ↔ Employee ↔ Department relationships
from shadow purchase transaction data to detect collusive procurement rings.

Algorithm:
  1. Build adjacency graph: each shared employee/dept between two vendors = edge weight
  2. Compute degree centrality and betweenness proxy for each vendor node
  3. Detect clusters using union-find (connected components at risk-weighted thresholds)
  4. Score each ring by cumulative shadow exposure and frequency
  5. Return ring report with XAI explanation per ring

No external graph library required — pure Python adjacency list implementation.
"""

from __future__ import annotations
import datetime
import math
from collections import defaultdict
from typing import Optional


# ─────────────────────────────────────────────────────────────────────
#  UNION-FIND for Connected Component Detection
# ─────────────────────────────────────────────────────────────────────

class UnionFind:
    def __init__(self, nodes: list[str]):
        self.parent = {n: n for n in nodes}
        self.rank   = {n: 0  for n in nodes}

    def find(self, x: str) -> str:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: str, y: str):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def groups(self) -> dict[str, list[str]]:
        """Return {root: [members]} for all components with ≥ 1 member."""
        g: dict[str, list] = defaultdict(list)
        for node in self.parent:
            g[self.find(node)].append(node)
        return dict(g)


# ─────────────────────────────────────────────────────────────────────
#  MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────

class VendorRingDetector:
    """
    Detects vendor collusion rings from shadow purchase history.

    Usage:
        detector = VendorRingDetector()
        report   = detector.analyze(shadows, transactions, vendors)
    """

    # Edge weight threshold: two vendors must share ≥ this many employees
    # or departments to be considered linked
    LINK_THRESHOLD = 1

    # Minimum shadow count per vendor to be included in ring analysis
    MIN_SHADOW_COUNT = 1

    # Risk weight multipliers for ring scoring
    PAYMENT_RISK_WEIGHTS = {
        "Corporate Card": 1.5,
        "Expense Claim":  1.2,
        "Invoice":        0.8,
    }

    def analyze(
        self,
        shadows:      list,   # list of ShadowPurchase ORM objects
        transactions: dict,   # {txn_id: Transaction ORM object}
        vendors:      dict,   # {vendor_name: Vendor ORM object}
    ) -> dict:
        """
        Full ring-detection pipeline. Returns structured report.
        """
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ── Step 1: Aggregate shadow data per vendor ─────────────────
        vendor_stats: dict[str, dict] = defaultdict(lambda: {
            "shadow_count": 0,
            "total_amount": 0.0,
            "employees":    set(),
            "departments":  set(),
            "payment_types": defaultdict(int),
            "risk_scores":  [],
            "txn_ids":      [],
        })

        for shadow in shadows:
            txn = transactions.get(shadow.transaction_id)
            if not txn:
                continue
            vname = txn.vendor or "Unknown"
            vs    = vendor_stats[vname]
            vs["shadow_count"]    += 1
            vs["total_amount"]    += float(txn.amount or 0)
            vs["risk_scores"].append(float(shadow.risk_score or 0))
            vs["txn_ids"].append(txn.id)

            if txn.card_holder and txn.card_holder != "System":
                vs["employees"].add(txn.card_holder)
            if txn.department:
                vs["departments"].add(txn.department)
            if txn.payment_type:
                vs["payment_types"][txn.payment_type] += 1

        # Filter vendors with enough shadows to be significant
        active_vendors = {
            name: stats for name, stats in vendor_stats.items()
            if stats["shadow_count"] >= self.MIN_SHADOW_COUNT
        }

        vendor_names = list(active_vendors.keys())
        if len(vendor_names) < 2:
            return self._empty_report(now_str, "Insufficient vendor data for ring detection")

        # ── Step 2: Build adjacency graph ────────────────────────────
        # Edge weight = shared employees + shared departments
        adjacency: dict[str, dict[str, float]] = defaultdict(dict)

        for i, va in enumerate(vendor_names):
            for vb in vendor_names[i + 1:]:
                sa, sb = active_vendors[va], active_vendors[vb]

                shared_emp  = len(sa["employees"]  & sb["employees"])
                shared_dept = len(sa["departments"] & sb["departments"])
                weight      = shared_emp * 2.0 + shared_dept * 1.0

                if weight >= self.LINK_THRESHOLD:
                    adjacency[va][vb] = weight
                    adjacency[vb][va] = weight

        # ── Step 3: Compute degree centrality ────────────────────────
        centrality: dict[str, float] = {}
        max_possible = max(1, len(vendor_names) - 1)
        for vname in vendor_names:
            neighbours = adjacency.get(vname, {})
            centrality[vname] = round(len(neighbours) / max_possible, 3)

        # ── Step 4: Union-Find connected components ──────────────────
        uf = UnionFind(vendor_names)
        for va, neighbours in adjacency.items():
            for vb in neighbours:
                uf.union(va, vb)

        raw_groups = uf.groups()

        # ── Step 5: Score each ring ──────────────────────────────────
        rings = []
        ring_id = 1

        for root, members in raw_groups.items():
            if len(members) < 2:
                # Isolated node — not a ring
                continue

            # Aggregate ring-level stats
            ring_shadows    = sum(active_vendors[m]["shadow_count"]  for m in members)
            ring_exposure   = sum(active_vendors[m]["total_amount"]   for m in members)
            ring_avg_risk   = (
                sum(
                    sum(active_vendors[m]["risk_scores"]) / max(1, len(active_vendors[m]["risk_scores"]))
                    for m in members
                ) / len(members)
            )

            # Payment type breakdown
            combined_payments: dict[str, int] = defaultdict(int)
            for m in members:
                for ptype, cnt in active_vendors[m]["payment_types"].items():
                    combined_payments[ptype] += cnt

            # Dominant payment risk
            dominant_ptype  = max(combined_payments, key=combined_payments.get) if combined_payments else "Unknown"
            payment_weight  = self.PAYMENT_RISK_WEIGHTS.get(dominant_ptype, 1.0)

            # Ring risk score: composite of avg risk, exposure density, payment pattern
            exposure_factor = math.log1p(ring_exposure) / 15.0  # normalized log scale
            ring_risk       = min(1.0, round(
                (ring_avg_risk * 0.45)
                + (exposure_factor * 0.35)
                + ((payment_weight - 0.8) / 1.4 * 0.20),
                3
            ))

            # Severity classification
            if ring_risk > 0.65:
                severity = "Critical"
                severity_color = "#ef4444"
            elif ring_risk > 0.40:
                severity = "High"
                severity_color = "#f97316"
            elif ring_risk > 0.20:
                severity = "Medium"
                severity_color = "#f59e0b"
            else:
                severity = "Low"
                severity_color = "#22c55e"

            # Shared attributes
            shared_employees:   set[str] = set()
            shared_departments: set[str] = set()
            for mi, ma in enumerate(members):
                for mb in members[mi + 1:]:
                    shared_employees   |= active_vendors[ma]["employees"] & active_vendors[mb]["employees"]
                    shared_departments |= active_vendors[ma]["departments"] & active_vendors[mb]["departments"]

            # XAI explanation
            explanation_factors = _build_ring_explanation(
                members, active_vendors, shared_employees, shared_departments,
                ring_avg_risk, ring_exposure, dominant_ptype, adjacency
            )

            # Individual member profiles
            member_profiles = []
            for m in sorted(members, key=lambda x: active_vendors[x]["shadow_count"], reverse=True):
                ms          = active_vendors[m]
                avg_r       = sum(ms["risk_scores"]) / max(1, len(ms["risk_scores"]))
                vendor_obj  = vendors.get(m)
                member_profiles.append({
                    "vendor_name":   m,
                    "shadow_count":  ms["shadow_count"],
                    "total_exposure": round(ms["total_amount"], 2),
                    "avg_risk_score": round(avg_r, 3),
                    "employees":     sorted(ms["employees"]),
                    "departments":   sorted(ms["departments"]),
                    "risk_level":    vendor_obj.risk_level if vendor_obj else "Unknown",
                    "approved":      vendor_obj.approved   if vendor_obj else False,
                    "centrality":    centrality.get(m, 0),
                    "dominant_payment": dominant_ptype,
                })

            rings.append({
                "ring_id":            f"VR-{ring_id:03d}",
                "members":            members,
                "member_count":       len(members),
                "member_profiles":    member_profiles,
                "ring_risk_score":    ring_risk,
                "severity":           severity,
                "severity_color":     severity_color,
                "total_shadow_count": ring_shadows,
                "total_exposure":     round(ring_exposure, 2),
                "avg_risk_score":     round(ring_avg_risk, 3),
                "shared_employees":   sorted(shared_employees),
                "shared_departments": sorted(shared_departments),
                "dominant_payment":   dominant_ptype,
                "explanation_factors": explanation_factors,
                "edge_weight_summary": {
                    va: {vb: round(w, 1) for vb, w in adjacency[va].items() if vb in members}
                    for va in members if va in adjacency
                },
            })
            ring_id += 1

        # ── Step 6: Sort rings by risk ────────────────────────────────
        rings.sort(key=lambda r: r["ring_risk_score"], reverse=True)

        # ── Step 7: Isolated (solo) high-risk vendors ────────────────
        isolated_vendors = []
        for vname in vendor_names:
            if not adjacency.get(vname):  # No edges = isolated
                vs       = active_vendors[vname]
                avg_risk = sum(vs["risk_scores"]) / max(1, len(vs["risk_scores"]))
                if avg_risk > 0.5 or vs["shadow_count"] >= 3:
                    isolated_vendors.append({
                        "vendor_name":   vname,
                        "shadow_count":  vs["shadow_count"],
                        "avg_risk_score": round(avg_risk, 3),
                        "total_exposure": round(vs["total_amount"], 2),
                        "note":          "High-risk isolated vendor — monitor independently",
                    })

        return {
            "status":            "success",
            "generated_at":      now_str,
            "vendors_analyzed":  len(vendor_names),
            "rings_detected":    len(rings),
            "total_exposure":    round(sum(r["total_exposure"] for r in rings), 2),
            "critical_rings":    sum(1 for r in rings if r["severity"] == "Critical"),
            "rings":             rings,
            "isolated_vendors":  isolated_vendors[:10],
            "graph_meta": {
                "nodes":         len(vendor_names),
                "edges":         sum(len(v) for v in adjacency.values()) // 2,
                "algorithm":     "Union-Find Connected Components + Risk Scoring",
                "link_threshold": self.LINK_THRESHOLD,
            },
        }

    # ── helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _empty_report(now_str: str, reason: str) -> dict:
        return {
            "status":           "no_data",
            "generated_at":     now_str,
            "vendors_analyzed": 0,
            "rings_detected":   0,
            "total_exposure":   0.0,
            "critical_rings":   0,
            "rings":            [],
            "isolated_vendors": [],
            "message":          reason,
            "graph_meta":       {"nodes": 0, "edges": 0, "algorithm": "N/A"},
        }


def _build_ring_explanation(
    members:       list[str],
    vendor_stats:  dict,
    shared_emp:    set[str],
    shared_dept:   set[str],
    avg_risk:      float,
    exposure:      float,
    dominant_ptype: str,
    adjacency:     dict,
) -> list[str]:
    """Generate human-readable XAI factors for a detected ring."""
    factors = []

    if len(members) >= 3:
        factors.append(
            f"Multi-vendor ring detected: {len(members)} vendors share procurement channels"
        )
    else:
        factors.append(
            f"Vendor pair linked by shared procurement actors"
        )

    if shared_emp:
        emp_list = ", ".join(list(shared_emp)[:3])
        factors.append(
            f"Common card-holders across vendors: {emp_list}"
            + (" (and more)" if len(shared_emp) > 3 else "")
        )

    if shared_dept:
        dept_list = ", ".join(list(shared_dept)[:3])
        factors.append(f"Purchases routed through shared departments: {dept_list}")

    if dominant_ptype in ("Corporate Card", "Expense Claim"):
        factors.append(
            f"Dominant payment channel '{dominant_ptype}' bypasses standard PO controls"
        )

    if avg_risk > 0.60:
        factors.append(
            f"Aggregate AI risk score {avg_risk:.0%} — above critical threshold"
        )
    elif avg_risk > 0.40:
        factors.append(f"Elevated aggregate risk score: {avg_risk:.0%}")

    if exposure > 10000:
        factors.append(
            f"Total financial exposure ₹{exposure:,.0f} across ring — material audit risk"
        )
    elif exposure > 3000:
        factors.append(f"Significant exposure: ₹{exposure:,.0f} untracked spend")

    # Edge density
    total_possible_edges = len(members) * (len(members) - 1) / 2
    actual_edges = sum(
        1 for va in members for vb in members
        if va < vb and vb in adjacency.get(va, {})
    )
    density = actual_edges / max(1, total_possible_edges)
    if density >= 0.7:
        factors.append(
            f"High graph density ({density:.0%}) — vendors appear tightly coordinated"
        )

    return factors


# ── Singleton ─────────────────────────────────────────────────────────
vendor_ring_detector = VendorRingDetector()


# =============================================================================
# F5: Supplier Network Graph (Tier 1/2/3 + Disruption Risk)
# =============================================================================

class SupplierNetworkGraph:
    """
    Builds a structured supply chain graph showing:
      - Vendor tier (1=direct, 2=sub-supplier, 3=raw material)
      - Which departments depend on each vendor
      - Alternative vendors for each supplier
      - Disruption score: how badly operations suffer if this vendor fails

    Disruption formula:
        score = (dependent_dept_count × 0.3) / max(alternative_count, 1)
        capped at 1.0
    """

    def build(self, db) -> dict:
        """
        Build the full supplier network graph from the database.
        Returns: {vendor_name: {tier, trust_score, risk_level, dependents, alternatives, disruption_score}}
        """
        from database import Vendor, Transaction

        vendors = db.query(Vendor).all()

        # Build dept → vendor usage map from transaction history
        dept_vendor_pairs = (
            db.query(Transaction.department, Transaction.vendor)
            .filter(Transaction.vendor.isnot(None))
            .group_by(Transaction.department, Transaction.vendor)
            .all()
        )

        dependents: dict[str, set] = {}
        for dept, vendor_name in dept_vendor_pairs:
            if vendor_name:
                dependents.setdefault(vendor_name, set()).add(dept)

        graph = {}
        for v in vendors:
            alts = [
                a.strip()
                for a in (v.alternative_vendors or "").split(",")
                if a.strip()
            ]
            vendor_deps = dependents.get(v.name, set())
            graph[v.name] = {
                "tier":              v.tier or 1,
                "trust_score":       v.trust_score,
                "risk_level":        v.risk_level,
                "esg_score":         getattr(v, "esg_score", 50.0),
                "carbon_rating":     getattr(v, "carbon_rating", "C"),
                "dependents":        sorted(vendor_deps),
                "alternatives":      alts,
                "disruption_score":  self.disruption_score(vendor_deps, alts),
            }
        return graph

    @staticmethod
    def disruption_score(dependents: set, alternatives: list) -> float:
        """
        Higher score = more disruption if this vendor goes offline.
        Max = 1.0 (many dependents, no alternatives).
        """
        score = (len(dependents) * 0.3) / max(len(alternatives), 1)
        return round(min(score, 1.0), 3)


# Singleton
supplier_network_graph = SupplierNetworkGraph()
