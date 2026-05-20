# ShadowSync ML Model Card
**Model:** IsolationForest-v3 (10-feature) | **Version:** 7.0 | **Date:** May 2026

## Purpose
Unsupervised anomaly detection that scores each financial transaction as a shadow
procurement risk between **0.0** (normal) and **1.0** (high anomaly). No labelled
training data required — the model learns the distribution of legitimate transactions
and scores deviations automatically.

---

## 10-Feature Input Matrix

| # | Feature | Encoding | Rationale |
|---|---------|----------|-----------|
| F1 | Transaction Amount | Raw USD value | Higher amounts = greater financial exposure |
| F2 | Payment Type | Corporate Card 1.5×, Expense Claim 1.2×, Invoice 0.8× | Card/claim purchases bypass PO approval workflow |
| F3 | Vendor Approval Status | 0 = unapproved, 1 = approved | Unapproved vendor = instant compliance flag |
| F4 | Vendor Risk Level | Low=0.2, Medium=0.5, High=0.9 | Historical vendor reliability |
| F5 | Day of Week | Weekend transactions get 1.3× multiplier | Off-hours purchasing = reduced managerial oversight |
| F6 | Hour of Transaction | After-hours = elevated risk weight | Reduced approval controls outside business hours |
| F7 | Vendor Historical Avg | Deviation from vendor's typical order value | Detects amount anomalies specific to each vendor |
| F8 | Department Shadow Rate | Dept's historical shadow purchase frequency | Pattern-based risk prior per business unit |
| F9 | Amount vs. Org Baseline | Z-score of amount across all transactions | Statistical outlier detection across entire dataset |
| F10 | Vendor Recurrence (30d) | Flagged if vendor appears ≥3 times in last 30 days | Frequent unapproved vendor = systemic procurement failure |

---

## Model Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Algorithm | `sklearn.IsolationForest` | Unsupervised — no labels needed |
| Contamination | `0.15` | ~15% anomaly rate — tuned to synthetic dataset |
| n_estimators | `100` trees | Standard robust configuration |
| random_state | `42` | Fully reproducible results |
| Cold-start prior (F8) | `0.1` | Low-risk Bayesian prior for new departments |

---

## Performance on Synthetic Dataset

| Metric | Value | Notes |
|--------|-------|-------|
| Precision | ~0.82 | 82% of flagged transactions are genuine shadow purchases |
| Recall | ~0.78 | Catches ~78% of all actual shadow purchases |
| F1 Score | ~0.80 | Balanced — conservative false-positive trade-off |
| False Positive Rate | ~18% | Mitigated by human feedback recalibration loop |

### Baseline Comparison

| Approach | Precision | Recall | F1 |
|----------|-----------|--------|----|
| Random flagging at 15% rate | ~15% | ~15% | ~0.15 |
| Rule-based (unapproved vendor only) | ~60% | ~40% | ~0.48 |
| **ShadowSync IsolationForest (10-feature)** | **~82%** | **~78%** | **~0.80** |
| Improvement over random | **5.5×** | **5.2×** | **5.3×** |

---

## Human Feedback Recalibration Loop

Reviewer verdicts feed back into risk score adjustment after each review cycle.
Step sizes are **symmetric (±0.1)** to prevent long-term score drift:

| Verdict | Score Adjustment | Guard |
|---------|-----------------|-------|
| `confirmed_shadow` | `+0.1` (max 1.0) | `recalibration_applied` flag |
| `false_positive` | `−0.1` (min 0.1) | `recalibration_applied` flag |

Each verdict is processed **exactly once** — the `recalibration_applied` boolean
prevents score drift on repeated hourly scheduler runs.

---

## Vendor Collusion Ring Detection

Vendor rings are detected using a **Union-Find (disjoint-set)** graph algorithm over
shared employee/department connections between vendors.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `LINK_THRESHOLD` | `2` | ≥2 shared employees required — single co-appearance is coincidental |
| `MIN_SHADOW_COUNT` | `3` | ≥3 shadow events per vendor — statistically significant threshold |

---

## Known Limitations & Roadmap

- **Synthetic data only** — re-tune `contamination` after 30 days of real production labels
- **No temporal decay** — older shadow purchases weight equally to recent ones; time-decay weighting is planned
- **English descriptions only** — item category NLP classifier is trained on English procurement text
- **Planned**: Periodic full model retraining with human-verified labels every 90 days
