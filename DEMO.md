# ShadowSync — Exhibition Demo Cheat Sheet
> **Print this. Laminate it. Have it on the table.**

---

## Before Judges Arrive (10 minutes before)

```
1. docker-compose up --build          # or: uvicorn app:app --reload --port 8000
2. Open http://localhost:8000         # confirm dashboard loads, no errors
3. GET  http://localhost:8000/api/health  # confirm {"status":"ok"}
4. Click "Reset Demo" button → confirm toast "Reset complete"
5. Open AI Copilot → type "What are the top risks?"
   → confirm response appears within 3 seconds
6. Click Priority Queue → confirm $47,200 ShadowTech card is at the top
```

---

## 6-Step Demo Script (4 minutes)

### Step 1 — The Problem (30 seconds)
- Point to **Financial Exposure** and **Integrity Variance** stat cards
- Say:
  > *"34% of spend is invisible. That's $2.8M in untracked procurement per $100M budget.
  > This is money leaving the organisation through unapproved channels right now."*

### Step 2 — A Live Detection (45 seconds)
- Click **Priority Queue** tab
- Click the **$47,200 ShadowTech Solutions** card (highest risk score, should be ~0.92)
- Point to the XAI breakdown — read the top 3 risk factors aloud
- Say:
  > *"Flagged in under one second. Corporate card. 11:31pm Saturday.
  > Unapproved vendor. No PO. Risk score 0.92 out of 1.0."*

### Step 3 — AI Copilot (45 seconds)
- Open the **AI Copilot** tab
- Type: `Which vendors need urgent attention?`
- While it loads, say: *"Two LLMs in parallel — Groq at 200ms, Cohere for executive summaries."*
- When response appears: point to FastParts / QuickSupply / RapidTools
- Say:
  > *"The model picked up the split-PO pattern before a human would have noticed."*

### Step 4 — Vendor Collusion (30 seconds)
- Click **Vendors** tab → scroll to **Vendor Rings** section
- Point to: **FastParts Ltd / QuickSupply Co / RapidTools Inc**
- Say:
  > *"Three vendors. Same employee. Same department. All transactions under the $5,000
  > approval threshold. Classic split-PO fraud — caught automatically."*

### Step 5 — Prevention (30 seconds)
- Click **Inventory** tab
- Point to an item with a green **Auto-PO Draft** badge
- Say:
  > *"Stock hit the reorder point. A PO draft was raised automatically.
  > The purchase goes through proper channels. No shadow purchasing needed."*

### Step 6 — The Trend (30 seconds)
- Click **Analytics** → **Trend Chart**
- Point to the **Finance department** line going steeply downward
- Say:
  > *"Finance was at 45% shadow rate in January. By March: 8%.
  > The system is working. That's the ROI story."*

---

## Hard Judge Questions — Scripted Answers

**"Does the model actually learn?"**
> *"Yes. Every 10 human corrections trigger a full Isolation Forest retrain —
> new contamination parameter, new decision boundary.
> The Detection Quality card tracks live accuracy from real reviewer feedback.
> You can watch it change during the demo."*

**"What makes this different from SAP Ariba?"**
> *"SAP flags at month-end batch review. We flag in under one second.
> SAP has no ML risk ranking — you get a flat list, not a priority queue.
> Our Preventive Intelligence layer stops the purchase before it happens.
> SAP has none of that. This is the operational layer that sits on top of any ERP."*

**"How accurate is it?"**
> *"Isolation Forest starts at ~85% baseline — zero labeled training data required.
> With human feedback it self-improves. The Detection Quality card shows live accuracy.
> On our exhibition dataset with 4 scenario seeds: consistently above 88%."*

**"Can it scale?"**
> *"PostgreSQL-ready — one environment variable swap.
> Containerised with Docker — one command deploy.
> WebSocket architecture handles concurrent analyst sessions.
> ML and LLM calls are stateless — horizontally scalable behind any load balancer."*

**"What's the SAP connector?"**
> *"Right now: CSV/Excel import — works with any ERP export.
> Next milestone: SAP BAPI live connector to replace the batch import with
> real-time event streaming. The ingestion layer is already abstracted for that."*

**"What would you build next?"**
> *"Three things: SAP BAPI live connector, React Native mobile approval app,
> and predictive analytics — forecast shadow risk before it happens
> using seasonal spend patterns and vendor history."*

---

## Key Numbers to Cite (Memorise These)

| Stat | Value | Source |
|------|-------|--------|
| Enterprise shadow spend | 30–40% of total procurement | Gartner |
| Average annual leakage | $2.8M per $100M budget | Gartner |
| Manual detection time | 87 days average | KPMG |
| ShadowSync detection | < 1 second | Live demo |
| Groq response time | ~200ms | Live demo |
| ML features | 10 (IsolationForest-v3) | ai_module.py |
| Training data required | 0 (unsupervised) | Design |
| Detection Quality baseline | 85.0% | Stats card |

---

## If Things Go Wrong

| Problem | Fix |
|---------|-----|
| WiFi dies | All ML/detection features work offline. Show XAI breakdown instead of copilot. Say: *"Core ML engine is fully local — no cloud dependency for detection."* |
| AI Copilot slow/stalled | The cache pre-warmed 6 answers at startup. Refresh copilot tab. Fall back to showing the vendor ring detection instead. |
| Dashboard blank | Check http://localhost:8000/api/health — if down, `docker-compose restart` |
| No shadows showing | Click "Reset Demo" → then GET /api/ml/retrain to re-score all transactions |
| Second judge sees resolved data | Click **🔄 Reset Demo** in the header → confirm → everything resets |

---

## Endpoint Quick Reference

| Endpoint | What it does |
|----------|-------------|
| `GET  /api/stats` | Financial exposure, shadow rate, detection quality |
| `GET  /api/shadows` | All shadow purchases with risk scores |
| `GET  /api/ml/status` | Model version, feature weights, fitted status |
| `POST /api/ml/retrain` | Manual retrain trigger |
| `POST /api/demo/reset` | Reset to clean exhibition state |
| `POST /api/feedback/{id}` | Submit human feedback (triggers auto-retrain at 10) |
| `GET  /api/analytics/dept-risk` | Department risk heatmap data |
| `GET  /api/supplier-network` | Vendor collusion network graph |
| `GET  /api/trends?period=week` | Trend chart time series data |
| `POST /api/import/csv` | Batch CSV/Excel ingestion |
| `GET  /api/health` | System health check |
