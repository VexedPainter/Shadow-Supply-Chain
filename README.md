<div align="center">

<!-- Animated Header Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:161b22,100:1f6feb&height=220&section=header&text=ShadowSync&fontSize=72&fontColor=58a6ff&fontAlignY=35&desc=AI-Powered%20Shadow%20Procurement%20Detection&descSize=18&descAlignY=55&animation=fadeIn" width="100%"/>

<!-- Dynamic Badges -->
<p>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=for-the-badge&logo=meta&logoColor=white" />
  <img src="https://img.shields.io/badge/Cohere-Command_A-3A76F0?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>
<p>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Production-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Scikit--Learn-ML_Engine-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" />
  <img src="https://img.shields.io/badge/SAP-Connector-0FAAFF?style=for-the-badge&logo=sap&logoColor=white" />
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
</p>

<p>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/🚀_Quick_Start-blue?style=for-the-badge" /></a>
  <a href="#-key-features"><img src="https://img.shields.io/badge/✨_Features-purple?style=for-the-badge" /></a>
  <a href="#-ai-copilot"><img src="https://img.shields.io/badge/🤖_AI_Copilot-green?style=for-the-badge" /></a>
  <a href="#-api-reference"><img src="https://img.shields.io/badge/📡_API_Docs-orange?style=for-the-badge" /></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/🔐_Security-red?style=for-the-badge" /></a>
</p>

<br/>

> **Enterprise-grade real-time platform that detects shadow purchases — unauthorized, untracked procurement spending — using Machine Learning anomaly detection and a dual-LLM AI Copilot (Groq + Cohere).**

</div>

---

## 🎯 The Problem We Solve

In large organizations, **shadow procurement** (maverick spending) accounts for **30–40% of total procurement spend** bypassing official PO systems — that's **$2.8M leakage per $100M budget** *(Gartner)*.

<table>
<tr>
<td width="50%">

### ❌ Without ShadowSync
- Untracked corporate card purchases
- Unapproved vendor expense claims
- After-hours emergency buys with no PO
- **87 days** average manual detection time *(KPMG)*
- Zero visibility into procurement compliance

</td>
<td width="50%">

### ✅ With ShadowSync
- **< 1 second** AI-powered detection
- Dual-LLM copilot for instant risk analysis
- Vendor collusion ring detection
- Preventive auto-PO drafting
- Real-time WebSocket dashboard with alerts

</td>
</tr>
</table>

---

## ⚡ Quick Start

<table>
<tr><td>

### 🐳 Docker (Recommended)
```bash
git clone https://github.com/VexedPainter/Shadow-Supply-Chain.git
cd Shadow-Supply-Chain

# Set your API keys
cp .env.example .env
# Edit .env with your GROQ_API_KEY and COHERE_API_KEY

docker-compose up --build
# → Dashboard: http://localhost:8000
```

</td><td>

### 🐍 Manual Setup
```bash
git clone https://github.com/VexedPainter/Shadow-Supply-Chain.git
cd Shadow-Supply-Chain

pip install -r requirements.txt
python generate_data.py

python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
# → Dashboard: http://localhost:8000
```

</td></tr>
</table>

> **Default Login:** Username from `ADMIN_USERNAME` env var (default: `admin`), Password from `ADMIN_PASSWORD` env var.
> ⚠️ Always set `ADMIN_PASSWORD` via environment variable before deploying. See [Security Guide](SECURITY.md).

---

## ✨ Key Features

<table>
<tr>
<td align="center" width="33%">
<h3>🔍 ML Detection Engine</h3>
<p>Isolation Forest anomaly detection (v3) with 10 engineered features. See <a href="MODEL_CARD.md">MODEL_CARD.md</a>. Auto-retrains securely without score drift. 85%+ baseline accuracy — zero labeled data needed.</p>
</td>
<td align="center" width="33%">
<h3>🤖 Dual-LLM AI Copilot</h3>
<p>Groq (LLaMA 3.3 70B) at ~200ms for chat & deep analysis. Cohere (Command A) for executive summaries & vendor insights. Conversational natural language interface.</p>
</td>
<td align="center" width="33%">
<h3>📊 Real-Time Dashboard</h3>
<p>WebSocket-powered live feed. 4 interactive Chart.js visualizations. AI-ranked Priority Queue. Glassmorphic "Kinetic Ledger" design system.</p>
</td>
</tr>
<tr>
<td align="center" width="33%">
<h3>🕸️ Vendor Collusion Detection</h3>
<p>Graph analysis detects split-PO fraud rings — multiple shell vendors, same employee, amounts under approval thresholds. Strict thresholds prevent false positives. Automatic escalation.</p>
</td>
<td align="center" width="33%">
<h3>🛡️ Preventive Intelligence</h3>
<p>Auto-PO drafting when inventory hits reorder points. Predictive department risk scoring. Stops shadow purchases before they happen.</p>
</td>
<td align="center" width="33%">
<h3>🔗 SAP BAPI Connector</h3>
<p>Live RFC connection to SAP ERP (EKKO/EKPO/RBKP fields). Graceful simulation fallback with authentic field schemas. Works with any ERP via CSV/Excel import.</p>
</td>
</tr>
<tr>
<td align="center" width="33%">
<h3>📱 Multi-Channel Alerts</h3>
<p>Email (SMTP), Slack webhooks, and Firebase Cloud Messaging push notifications. Critical shadow alerts reach managers instantly on any device.</p>
</td>
<td align="center" width="33%">
<h3>📄 Export & Reporting</h3>
<p>Executive PDF reports with styled tables. CSV & Excel bulk exports. Auto-generated recommendations with severity scoring.</p>
</td>
<td align="center" width="33%">
<h3>🔐 Enterprise Security</h3>
<p>JWT session auth with RBAC (admin/analyst/auditor). Fernet field-level encryption. Complete audit trail. SOC 2 readiness checklist included.</p>
</td>
</tr>
</table>

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER                            │
│                                                                         │
│   SAP BAPI (Live/Sim) ──┐                                              │
│   CSV/Excel Import ─────┼──► Unified Transaction Pipeline               │
│   ERP Batch Export ─────┘                                               │
│                                                                         │
│   Purchase Orders ────► Cross-Reference Engine                          │
│   Vendor Registry ────► Trust Score Database                            │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      DETECTION ENGINE (AI/ML)                           │
│                                                                         │
│   PO Matching ─────► Shadow Flagging ─────► Isolation Forest Scoring    │
│   (vendor+amount       (unmatched =          (10 features → risk        │
│    ±5%, date ±7d)       shadow candidate)      score 0.0–1.0)           │
│                                                                         │
│   NLP Category ────► Vendor Trust ────► Collusion Graph ────► Alerts    │
│   Classification      Score Update      Ring Detection        (Email/   │
│                                                                Slack/   │
│                                                                Push)    │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE & RESPONSE LAYER                        │
│                                                                         │
│   📊 Dashboard ───── Stats, Charts, Live Feed, Urgent Actions           │
│   🤖 AI Copilot ──── Groq Chat + Cohere Summaries (dual-LLM)           │
│   📋 Priority Queue ─ AI-ranked by severity with XAI breakdown          │
│   🛡️ Prevention ──── Auto-PO Drafts, Dept Risk Predictions             │
│   📄 Exports ──────── PDF Reports, CSV, Excel                           │
│   🔍 Audit Trail ──── Full compliance logging                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 AI & ML Pipeline

### Feature Engineering (10+ Features)

```python
Features = {
    "amount":           float,    # Transaction dollar value
    "hour_of_day":      int,      # After-hours = higher risk
    "day_of_week":      int,      # Weekend purchases = higher risk
    "amount_deviation": float,    # Deviation from vendor's average
    "vendor_risk":      float,    # Vendor risk level (0–1)
    "vendor_approved":  int,      # 1 = approved, 0 = unapproved
    "payment_type":     int,      # Invoice=0, Card=1, Expense=2
    "is_recurring":     int,      # Recurring pattern flag
    "dept_risk":        float,    # Department's historical shadow rate
    "amount_category":  int,      # Binned amount range
}
```

### Detection Pipeline

```
Raw Transaction → Feature Extraction → PO Matching → If Unmatched:
  → Isolation Forest Scoring → Category Classification
  → Vendor Trust Update → Collusion Graph Check
  → Priority Queue Ranking → Alert Dispatch (Email/Slack/Push)
  → Store as ShadowPurchase → WebSocket Alert to Dashboard
```

| Parameter | Value |
|-----------|-------|
| **Algorithm** | Isolation Forest v3 (Unsupervised) |
| **Training Data Required** | Zero — learns normal patterns automatically |
| **Risk Thresholds** | > 0.6 High · 0.35–0.6 Medium · < 0.35 Low |
| **Recalibration Guard** | Idempotent feedback loop prevents unbounded score drift |
| **Baseline Accuracy** | 85%+ (improves with feedback loop) |

---

## 🤖 AI Copilot

The dual-LLM AI Copilot provides a conversational interface to your supply chain data.

| Capability | Provider | Speed | Use Case |
|------------|----------|-------|----------|
| **Chat & Analysis** | Groq (LLaMA 3.3 70B) | ~200ms | *"What are the top risks right now?"* |
| **Deep Shadow Analysis** | Groq (LLaMA 3.3 70B) | ~200ms | Root cause analysis of individual shadows |
| **Executive Summaries** | Cohere (Command A) | ~1s | C-suite risk landscape overview |
| **Vendor Insights** | Cohere (Command A) | ~1s | AI-generated vendor risk profiles |

**Context Injection:** The AI automatically receives live system context (transaction counts, exposure, high-risk vendors) before every response — ensuring answers are always data-driven.

### How to Use
1. Click the floating **🤖 AI button** (bottom-right corner)
2. Type your question in natural language
3. Use ⚡ for health check or 📊 for executive summary

---

## 🗄️ Database Schema

**11 interconnected tables** — SQLite for dev, PostgreSQL for production (auto-detected via `DATABASE_URL`).

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   transactions  │────►│ shadow_purchases │────►│ recommendations  │
│  id, date,      │     │  risk_score,     │     │  action_taken,   │
│  vendor, amount │     │  confidence,     │     │  priority        │
│  payment_type   │     │  status,         │     └──────────────────┘
│  department     │     │  priority_score  │
│  is_shadow      │     │  estimated_loss  │     ┌──────────────────┐
│  ai_risk_score  │     │  item_category   │────►│ behavior_metrics │
└─────────────────┘     └──────────────────┘     └──────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│    vendors      │     │   procurement    │     │  risk_snapshots  │
│  trust_score    │     │   (PO records)   │     │  total_exposure  │
│  risk_level     │     │                  │     │  shadow_rate     │
│  approved       │     │                  │     │  risk_level      │
└─────────────────┘     └──────────────────┘     └──────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   inventory     │     │  user_feedback   │     │   audit_log      │
│  quantity, sku  │     │  correct_label   │     │  action_type     │
│  reorder_level  │     │  feedback_text   │     │  performed_by    │
└─────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## 📡 API Reference

<details>
<summary><b>📊 Core Data APIs</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Dashboard statistics (exposure, shadow rate, quality) |
| `GET` | `/api/transactions` | All financial transactions with shadow flags |
| `GET` | `/api/shadows` | Detected shadow purchases with risk scores |
| `GET` | `/api/procurement` | Approved purchase orders |
| `GET` | `/api/vendors` | Vendor registry with trust scores |
| `GET` | `/api/inventory` | Current inventory levels |
| `GET` | `/api/audit` | Complete audit trail |
| `GET` | `/api/health` | System health check |

</details>

<details>
<summary><b>🤖 AI Copilot APIs</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ai/chat` | Chat with Groq LLM |
| `GET` | `/api/ai/analyze/{id}` | Deep analysis of a shadow purchase |
| `GET` | `/api/ai/summarize` | Executive risk summary (Cohere) |
| `GET` | `/api/ai/vendor-insight/{vendor}` | AI vendor risk assessment |
| `GET` | `/api/ai/health` | Groq & Cohere connectivity status |

</details>

<details>
<summary><b>⚡ Action & Operations APIs</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/shadows/{id}/resolve` | Convert shadow to approved PO |
| `POST` | `/api/shadows/{id}/dismiss` | Dismiss shadow alert |
| `GET` | `/api/priority-queue` | AI-ranked priority queue |
| `GET` | `/api/recommendations` | AI action recommendations |
| `POST` | `/api/feedback` | Submit human feedback |
| `GET` | `/api/trends` | Weekly trend analysis |
| `POST` | `/api/ml/retrain` | Manual ML model retrain |
| `GET` | `/api/ml/status` | Model version & feature weights |
| `GET` | `/api/analytics/dept-risk` | Department risk heatmap |
| `GET` | `/api/supplier-network` | Vendor collusion network graph |
| `POST` | `/api/import/csv` | Batch CSV/Excel ingestion |
| `POST` | `/api/demo/reset` | Reset to exhibition state |

</details>

<details>
<summary><b>📄 Export APIs</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/download/shadow-report` | PDF executive risk report |
| `GET` | `/api/download/csv` | CSV data export |
| `GET` | `/api/v2/generate-report` | Comprehensive PDF report |

</details>

<details>
<summary><b>🔧 System APIs</b></summary>

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/set-mode` | Switch Synthetic/Production datasets |
| `POST` | `/api/simulator/start` | Start real-time transaction simulator |
| `POST` | `/api/simulator/stop` | Pause transaction simulator |
| `WebSocket` | `/ws` | Real-time updates (stats, alerts, shadows) |

</details>

---

## 📁 Project Structure

```
Shadow-Supply-Chain/
│
├── 🚀 Core Application
│   ├── app.py                      # FastAPI server (4000+ lines) — routes, WebSocket, auth, simulator
│   ├── database.py                 # SQLAlchemy ORM models (11 tables) & DB initialization
│   ├── detection.py                # Shadow Detection Engine — PO matching, scoring, vendor trust
│   ├── ai_module.py                # ML pipeline — Isolation Forest, feature engineering, NLP
│   ├── ai_copilot.py               # Dual-LLM Copilot — Groq chat + Cohere summarization
│   ├── analytics.py                # Predictive department risk scoring engine
│   ├── preventive_intelligence.py  # Auto-PO drafting & prevention layer
│   ├── vendor_graph.py             # Vendor collusion network graph analysis
│   ├── recalibration.py            # ML model recalibration with human feedback
│   └── pdf_generator.py            # Executive PDF report generation
│
├── 🔗 Connectors
│   ├── connectors/sap.py           # SAP BAPI connector (live RFC + simulation fallback)
│   └── connectors/push.py          # Firebase Cloud Messaging push notifications
│
├── 📊 Data Layer
│   ├── generate_data.py            # Synthetic dataset generator (50+ transactions, 21 vendors)
│   ├── production_data.py          # Real-world SF infrastructure scenarios
│   ├── upgrade_db.py               # Database migration scripts
│   └── data/                       # CSV datasets (transactions, POs, vendors, inventory)
│
├── 🎨 Frontend
│   ├── static/index.html           # Main dashboard SPA
│   ├── static/app.js               # Frontend logic (2500+ lines)
│   ├── static/styles.css           # "Kinetic Ledger" design system
│   └── static/downloads/           # Generated PDF/CSV exports
│
├── 🐳 DevOps
│   ├── Dockerfile                  # Multi-stage container build
│   ├── docker-compose.yml          # Full stack (app + PostgreSQL)
│   ├── .github/workflows/ci.yml    # CI/CD — tests, security audit, Docker build
│   ├── render.yaml                 # Render.com deployment config
│   └── build.sh                    # Cloud build script
│
├── 🧪 Testing
│   ├── test_api.py                 # API integration test suite
│   ├── e2e_test.py                 # End-to-end system verification
│   ├── test_exports.py             # Export functionality tests
│   └── test_feedback.py            # Human feedback loop tests
│
├── 📋 Documentation
│   ├── README.md                   # This file
│   ├── DEMO.md                     # Exhibition demo cheat sheet
│   ├── MODEL_CARD.md               # Detailed ML architecture documentation
│   ├── SECURITY.md                 # SOC 2 audit readiness & security guide
│   └── FIXES_APPLIED.md            # Changelog of patches applied
│
├── 🔧 Configuration
│   ├── .env.example                # Environment variable template
│   ├── requirements.txt            # Pinned Python dependencies
│   └── .gitignore                  # Git exclusion rules
│
└── 🛠️ Dev Scripts
    └── _dev_scripts/               # Debug utilities, encoding fixers, DB checkers
```

---

## 🏗️ Technology Stack

<table>
<tr>
<td valign="top" width="50%">

### ⚙️ Backend
| Technology | Purpose |
|-----------|---------|
| **Python 3.11** | Core language |
| **FastAPI 0.115** | Async web framework |
| **SQLAlchemy 2.0** | Type-safe ORM |
| **SQLite / PostgreSQL** | Dev / Production DB |
| **Scikit-learn 1.5** | Isolation Forest ML |
| **Pandas 2.2** | Feature engineering |
| **Uvicorn / Gunicorn** | ASGI server |
| **APScheduler** | Scheduled tasks |
| **Cryptography** | Fernet encryption |
| **SlowAPI** | Rate limiting |

</td>
<td valign="top" width="50%">

### 🎨 Frontend & AI
| Technology | Purpose |
|-----------|---------|
| **HTML5 / CSS3 / JS** | Zero-framework SPA |
| **Chart.js 4.4** | Interactive visualizations |
| **WebSocket** | Real-time updates |
| **Inter Font** | Premium typography |
| **Groq** (LLaMA 3.3 70B) | Chat & deep analysis |
| **Cohere** (Command A) | Summaries & insights |
| **FPDF2** | PDF report generation |
| **OpenPyXL** | Excel exports |
| **Firebase Admin** | Mobile push notifications |
| **pyrfc** *(optional)* | SAP live connection |

</td>
</tr>
</table>

---

## 🔐 Security & Compliance

ShadowSync ships with a comprehensive [Security Guide](SECURITY.md) including:

- ✅ JWT session authentication with configurable TTL
- ✅ RBAC — `admin`, `analyst`, `auditor` roles
- ✅ Fernet field-level encryption (`FIELD_ENCRYPTION_KEY`)
- ✅ All secrets via environment variables (never hardcoded)
- ✅ Complete audit trail with action logging
- ✅ Auto-purge of records older than 7 years (GDPR/SOC 2)
- ✅ CORS restriction via `ALLOWED_ORIGINS`
- ✅ CI/CD security audit with `pip-audit`
- ✅ Docker health checks with graceful failure handling

---

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `ADMIN_USERNAME` | ✅ | Dashboard login username |
| `ADMIN_PASSWORD` | ✅ | Dashboard login password |
| `GROQ_API_KEY` | ✅ | Groq LLM API key |
| `COHERE_API_KEY` | ✅ | Cohere API key |
| `DATABASE_URL` | — | PostgreSQL URL (defaults to SQLite) |
| `FIELD_ENCRYPTION_KEY` | 🔶 | Fernet key for field encryption |
| `ALLOWED_ORIGINS` | 🔶 | CORS whitelist (comma separated) |
| `IOT_API_KEY` | 🔶 | Pre-shared key for IoT scanner devices |
| `SLACK_WEBHOOK_URL` | — | Slack alerts webhook |
| `ALERT_EMAIL_USER` / `_PASS` / `_TO` | — | Email alert configuration |
| `FIREBASE_CREDENTIALS_PATH` | — | FCM push notification credentials |
| `SAP_HOST` / `SAP_USER` / `SAP_PASSWORD` | — | SAP live connector |

> 🔶 = Recommended for production

---

## 🖥️ Dashboard Overview

| Tab | Description |
|-----|-------------|
| **Overview** | Stats cards, 4 interactive charts, live feed, urgent actions, trend insights |
| **Priority Queue** | AI-ranked shadows by severity — Critical → High → Medium → Low |
| **Telemetric Alerts** | Shadow detections with approve/review/reject actions |
| **Transactions** | Full financial ledger with shadow flags |
| **Procurement** | Approved POs from ERP system |
| **Vendors & Risk** | Vendor registry with trust scores & collusion rings |
| **Inventory** | Stock levels, reorder alerts, auto-PO badges |
| **Analytics** | Department trends, predictive risk scoring |
| **Audit Trail** | Complete compliance action log |
| **AI Copilot** | Conversational LLM interface with provider status |

---

## 🔮 Roadmap

- [x] ~~Docker containerization~~ ✅
- [x] ~~CI/CD with GitHub Actions~~ ✅
- [x] ~~SAP BAPI connector~~ ✅
- [x] ~~Multi-channel alerts (Email/Slack/Push)~~ ✅
- [x] ~~PostgreSQL production support~~ ✅
- [x] ~~SOC 2 security compliance~~ ✅
- [x] ~~Predictive department risk analytics~~ ✅
- [ ] OAuth 2.0 / SAML enterprise SSO
- [ ] React Native mobile approval app
- [ ] Predictive seasonal spend forecasting
- [ ] Multi-currency global procurement
- [ ] Kubernetes Helm chart deployment

---

## 🧪 Testing

```bash
# Run API integration tests
python test_api.py

# Run end-to-end verification
python e2e_test.py

# Run export tests
python test_exports.py
```

CI/CD runs automatically on push to `main` or `develop` via [GitHub Actions](.github/workflows/ci.yml) — includes dependency security audit, API tests, and Docker build verification.

---

## 📊 Key Metrics

<div align="center">

| Metric | Value |
|--------|-------|
| 🕐 Shadow Detection Speed | **< 1 second** |
| 🤖 Groq LLM Response Time | **~200ms** |
| 🎯 ML Baseline Accuracy | **85%+** |
| 📊 Engineered Features | **10+** |
| 🗄️ Database Tables | **11** |
| 📡 API Endpoints | **35+** |
| 📝 Lines of Code | **10,000+** |

</div>

---

## 👥 Team

Built by the **ShadowSync Engineering Team** as an enterprise supply chain intelligence platform.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:161b22,100:1f6feb&height=120&section=footer" width="100%"/>

**ShadowSync v7.0 — Exhibition Final**

*Protecting procurement integrity through AI-powered intelligence*

<p>
  <img src="https://img.shields.io/badge/Made_with-Python-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Powered_by-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/AI_by-Groq_+_Cohere-F55036?style=flat-square" />
</p>

</div>
