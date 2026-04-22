<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=for-the-badge&logo=meta&logoColor=white" />
  <img src="https://img.shields.io/badge/Cohere-Command_A-3A76F0?style=for-the-badge" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Scikit--Learn-ML_Engine-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" />
</p>

# 🛡️ Shadow Supply Chain Detection System

### AI-Powered Enterprise Procurement Intelligence & Anomaly Detection Platform

> An enterprise-grade real-time platform that detects **shadow purchases** (unauthorized, untracked procurement spending) using **Machine Learning anomaly detection** and **dual-LLM AI Copilot** (Groq + Cohere). The system monitors financial transactions, cross-references them against approved Purchase Orders, and flags discrepancies — helping organizations prevent financial leakage, ensure compliance, and maintain audit integrity.

---

## 📑 Table of Contents

1. [Problem Statement](#-problem-statement)
2. [How It Works](#-how-it-works--simplified-flow)
3. [Key Features](#-key-features)
4. [Technology Stack](#-technology-stack)
5. [System Architecture](#-system-architecture)
6. [AI & ML Pipeline](#-ai--ml-pipeline)
7. [AI Copilot (Groq + Cohere)](#-ai-copilot-groq--cohere)
8. [Database Schema](#-database-schema)
9. [API Endpoints](#-api-endpoints)
10. [Project Structure](#-project-structure)
11. [Setup & Installation](#-setup--installation)
12. [Running the Application](#-running-the-application)
13. [Default Credentials](#-default-credentials)
14. [API Keys Configuration](#-api-keys-configuration)
15. [Screenshots & Dashboard](#-screenshots--dashboard)
16. [Future Enhancements](#-future-enhancements)

---

## 🎯 Problem Statement

In large organizations, **shadow procurement** (also called *maverick spending*) accounts for **30–40% of total procurement spend** that bypasses official purchase order systems. This happens when employees:

- Use corporate credit cards for **emergency purchases** without raising a PO
- Submit **expense claims** for parts bought from unapproved vendors
- Make **after-hours/weekend purchases** from local hardware stores during emergencies

These untracked purchases create:
- ❌ **Financial leakage** — No price negotiation, no volume discounts
- ❌ **Compliance violations** — No audit trail, no approval workflow
- ❌ **Vendor risk** — Purchasing from unapproved, potentially unreliable vendors
- ❌ **Inventory blind spots** — Parts entering the facility without being tracked

**Our solution** automatically detects these shadow purchases using AI, flags them for review, and provides actionable intelligence to supply chain managers.

---

## ⚙️ How It Works — Simplified Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                         │
│                                                                 │
│   ERP Transactions ──► Financial records (invoices, cards,      │
│                        expense claims) are loaded into the DB   │
│                                                                 │
│   Purchase Orders ───► Approved POs from procurement system     │
│                        are loaded for cross-referencing          │
│                                                                 │
│   Vendor Registry ───► Approved/unapproved vendor database      │
│                        with trust scores and risk levels         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DETECTION ENGINE (AI/ML)                      │
│                                                                 │
│   Step 1: PO Matching ─── Match each transaction against POs   │
│           (vendor name + amount + date tolerance ±5 days)       │
│                                                                 │
│   Step 2: Shadow Flag ─── Unmatched transactions = potential   │
│           shadow purchases (flagged for AI scoring)             │
│                                                                 │
│   Step 3: ML Scoring ──── Isolation Forest anomaly detection   │
│           analyzes 10+ features to assign risk scores (0–1)     │
│                                                                 │
│   Step 4: Category AI ─── NLP classifies items into categories │
│           (Pumps, Electronics, Safety, etc.)                    │
│                                                                 │
│   Step 5: Vendor Trust ── Vendor trust scores updated based    │
│           on shadow purchase history and approval status        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    REAL-TIME DASHBOARD                           │
│                                                                 │
│   📊 Live Stats ──────── Financial exposure, shadow rate,       │
│                          detection quality, inventory health     │
│                                                                 │
│   📈 Charts ──────────── Risk trends, department heatmaps,     │
│                          category distribution, shadow ratios    │
│                                                                 │
│   🚨 Priority Queue ──── Ranked list of highest-risk shadows   │
│                          with estimated financial loss           │
│                                                                 │
│   🤖 AI Copilot ─────── Chat with Groq LLM for instant risk   │
│                          analysis and Cohere for summaries       │
│                                                                 │
│   📄 Export ──────────── PDF reports, CSV/Excel data exports    │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🔍 Core Detection
| Feature | Description |
|---------|-------------|
| **PO Matching Engine** | Cross-references every transaction against approved Purchase Orders using vendor name, amount (±15% tolerance), and date (±5 days) |
| **Isolation Forest ML** | Unsupervised anomaly detection model trained on 10+ features (amount, vendor risk, payment type, time patterns) |
| **Multi-Feature Scoring** | Risk scores (0–1) computed from amount anomaly, vendor trust, payment method, historical patterns, and department norms |
| **Item Category NLP** | AI-powered text classification of purchase descriptions into standard procurement categories |
| **Vendor Trust Scoring** | Dynamic trust scores (0–100) that decrease with each shadow purchase and increase with compliant behavior |

### 📊 Real-Time Dashboard
| Feature | Description |
|---------|-------------|
| **Live WebSocket Feed** | Real-time transaction stream with instant shadow alerts via WebSocket |
| **Interactive Charts** | 4 Chart.js visualizations: Risk Trend, Shadow Ratio, Department Heatmap, Category Distribution |
| **Priority Queue** | AI-ranked list of shadows by severity — Critical → High → Medium → Low |
| **Urgent Actions Panel** | Top 5 highest-risk items requiring immediate review |
| **Trend Insights** | Week-over-week shadow activity trends with department/vendor breakdowns |

### 🤖 AI Copilot (LLM-Powered)
| Feature | Provider | Description |
|---------|----------|-------------|
| **Conversational Chat** | Groq (LLaMA 3.3 70B) | Ask questions about risks, vendors, or procurement in natural language |
| **Risk Summarization** | Cohere (Command A) | Executive-level risk landscape summaries for C-suite stakeholders |
| **Deep Shadow Analysis** | Groq (LLaMA 3.3 70B) | Detailed root cause analysis of individual shadow purchases |
| **Vendor Insights** | Cohere (Command A) | AI-generated vendor risk profiles with actionable recommendations |

### 📋 Operations & Compliance
| Feature | Description |
|---------|-------------|
| **Audit Trail** | Complete log of all system actions, approvals, and status changes |
| **Human Feedback Loop** | Users can approve, reject, or correct AI predictions — improving accuracy over time |
| **PDF Reports** | Auto-generated executive summary PDFs with risk statistics and recommendations |
| **CSV/Excel Export** | Bulk data export for further analysis in spreadsheet tools |
| **Dual Data Mode** | Switch between Synthetic (demo) and Production (real-world SF infrastructure) datasets |

---

## 🏗️ Technology Stack

### Backend
| Technology | Purpose | Why We Chose It |
|-----------|---------|-----------------|
| **Python 3.10+** | Core language | Industry standard for AI/ML and data processing |
| **FastAPI** | Web framework | High-performance async API with auto-generated docs |
| **SQLAlchemy** | ORM | Type-safe database operations with relationship mapping |
| **SQLite** | Database | Zero-config embedded database, ideal for prototyping |
| **Scikit-learn** | ML Engine | Isolation Forest for unsupervised anomaly detection |
| **Pandas** | Data processing | Feature engineering and data manipulation |
| **Uvicorn** | ASGI server | Production-grade async web server |

### AI / LLM Providers
| Provider | Model | Purpose | Speed |
|----------|-------|---------|-------|
| **Groq** | `llama-3.3-70b-versatile` | Conversational AI chat, deep analysis | ~200ms inference |
| **Cohere** | `command-a-03-2025` | Risk summarization, vendor insights, classification | ~1s inference |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **HTML5 / CSS3** | Semantic markup with premium "Kinetic Ledger" design system |
| **Vanilla JavaScript** | Zero-framework, lightweight SPA with tab-based navigation |
| **Chart.js 4.4** | Interactive, responsive data visualizations |
| **WebSocket** | Real-time bidirectional communication for live updates |
| **Google Material Icons** | Consistent iconography across the dashboard |
| **Inter Font** | Premium typography from Google Fonts |

### Export & Reporting
| Technology | Purpose |
|-----------|---------|
| **FPDF2** | PDF report generation with formatted tables and charts |
| **OpenPyXL** | Excel (.xlsx) export with styled headers and formatting |
| **CSV module** | Lightweight data export for spreadsheet tools |

---

## 🧠 AI & ML Pipeline

### 1. Feature Engineering (10+ Features)

The detection engine extracts these features from each transaction for ML scoring:

```python
Features = {
    "amount":           float,    # Transaction dollar value
    "hour_of_day":      int,      # Time pattern (after-hours = riskier)
    "day_of_week":      int,      # Weekend purchases = riskier
    "amount_deviation": float,    # Deviation from vendor's average order
    "vendor_risk":      float,    # Vendor's risk level (0=Low, 1=High)
    "vendor_approved":  int,      # 1 if approved vendor, 0 if not
    "payment_type":     int,      # Encoded: Invoice=0, Card=1, Expense=2
    "is_recurring":     int,      # Pattern detection flag
    "dept_risk":        float,    # Department's historical shadow rate
    "amount_category":  int,      # Binned amount range (low/med/high)
}
```

### 2. Isolation Forest Model

```
Algorithm:   Isolation Forest (Unsupervised Anomaly Detection)
Rationale:   No labeled data needed — learns "normal" transaction patterns
             and flags outliers as potential shadows
Features:    10 numerical features per transaction
Output:      Anomaly score → mapped to risk_score (0.0 – 1.0)
Threshold:   score > 0.6 = High Risk, 0.35–0.6 = Medium, <0.35 = Low
```

### 3. Detection Pipeline Flow

```
Raw Transaction → Feature Extraction → PO Matching → If Unmatched:
  → Isolation Forest Scoring → Category Classification
  → Vendor Trust Update → Priority Queue Ranking
  → Store as ShadowPurchase → WebSocket Alert to Dashboard
```

---

## 🤖 AI Copilot (Groq + Cohere)

The AI Copilot provides a **conversational interface** to interact with your supply chain data using natural language.

### Architecture

```
┌──────────────────┐      ┌───────────────────────────┐
│   User's Chat    │      │      ai_copilot.py         │
│   Message        │─────►│                           │
│                  │      │  ┌──── Groq Client ────┐  │
│  "What are the   │      │  │  LLaMA 3.3 70B     │  │
│   top risks?"    │      │  │  • Chat responses   │  │
│                  │      │  │  • Deep analysis    │  │
│                  │      │  └────────────────────┘  │
│                  │      │                           │
│                  │      │  ┌──── Cohere Client ──┐  │
│                  │      │  │  Command A 2025     │  │
│                  │      │  │  • Risk summaries   │  │
│                  │      │  │  • Vendor insights  │  │
│                  │      │  │  • Classification   │  │
│                  │      │  └────────────────────┘  │
│                  │◄─────│                           │
│  AI Response     │      └───────────────────────────┘
└──────────────────┘
```

### How to Use the AI Copilot

1. **Click the floating 🤖 AI button** in the bottom-right corner of the dashboard
2. **Type your question** in natural language, for example:
   - *"What are the top risks right now?"*
   - *"Explain shadow purchase #5"*
   - *"Which vendors need attention?"*
   - *"Summarize this week's procurement health"*
3. **The AI responds** with data-driven analysis pulled from your live system context
4. **Quick Actions**: Use the ⚡ button for health check or 📊 button for executive risk summary

### Context Injection

The AI automatically receives live system context before each response:
- Total transactions, shadow count, financial exposure
- High-risk vendor count and pending actions
- This ensures responses are **always relevant** to your current data

---

## 🗄️ Database Schema

The system uses **SQLite** with **11 interconnected tables**:

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   transactions  │────►│ shadow_purchases │────►│ recommendations  │
│                 │     │                  │     │                  │
│  id (PK)        │     │  id (PK)         │     │  shadow_id (FK)  │
│  date           │     │  transaction_id  │     │  action_taken    │
│  vendor         │     │  risk_score      │     │  priority        │
│  amount         │     │  confidence      │     └──────────────────┘
│  description    │     │  status          │
│  payment_type   │     │  priority_score  │     ┌──────────────────┐
│  department     │     │  estimated_loss  │────►│ behavior_metrics │
│  is_shadow      │     │  item_category   │     │                  │
│  ai_risk_score  │     └──────────────────┘     │  department      │
└─────────────────┘                               │  shadow_count    │
                                                  │  risk_level      │
┌─────────────────┐     ┌──────────────────┐     └──────────────────┘
│    vendors      │     │   procurement    │
│                 │     │                  │     ┌──────────────────┐
│  id (PK)        │     │  id (PK)         │     │  risk_snapshots  │
│  name           │     │  vendor_id (FK)  │     │                  │
│  category       │     │  item            │     │  total_exposure  │
│  risk_level     │     │  amount          │     │  shadow_rate     │
│  approved       │     │  status          │     │  risk_level      │
│  trust_score    │     │  department      │     └──────────────────┘
└─────────────────┘     └──────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   inventory     │     │  user_feedback   │     │   audit_log      │
│                 │     │                  │     │                  │
│  name, sku      │     │  correct_label   │     │  action_type     │
│  quantity       │     │  feedback_text   │     │  details         │
│  unit_price     │     │  submitted_by    │     │  performed_by    │
│  reorder_level  │     └──────────────────┘     └──────────────────┘
└─────────────────┘
```

---

## 🔌 API Endpoints

### Core Data APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats` | Dashboard statistics (exposure, shadow rate, detection quality) |
| `GET` | `/api/transactions` | All financial transactions with shadow flags |
| `GET` | `/api/shadows` | Detected shadow purchases with risk scores |
| `GET` | `/api/procurement` | Approved purchase orders |
| `GET` | `/api/vendors` | Vendor registry with trust scores |
| `GET` | `/api/inventory` | Current inventory levels |
| `GET` | `/api/audit` | Complete audit trail log |

### AI Copilot APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ai/chat` | Send a chat message to Groq LLM |
| `GET` | `/api/ai/analyze/{id}` | Deep AI analysis of a specific shadow purchase |
| `GET` | `/api/ai/summarize` | Cohere-powered executive risk summary |
| `GET` | `/api/ai/vendor-insight/{vendor}` | AI vendor risk assessment |
| `GET` | `/api/ai/health` | Check Groq & Cohere connectivity status |

### Action APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/shadows/{id}/resolve` | Approve and convert shadow to PO |
| `POST` | `/api/shadows/{id}/dismiss` | Reject/dismiss a shadow alert |
| `GET` | `/api/priority-queue` | AI-ranked priority queue |
| `GET` | `/api/recommendations` | AI-generated action recommendations |
| `POST` | `/api/feedback` | Submit human feedback on AI predictions |
| `GET` | `/api/trends` | Weekly trend analysis |

### Export APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/download/shadow-report` | PDF executive risk report |
| `GET` | `/api/download/csv` | CSV data export |
| `GET` | `/api/v2/generate-report` | Comprehensive PDF report |

### System APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/set-mode` | Switch between Synthetic/Production datasets |
| `POST` | `/api/simulator/start` | Start real-time transaction simulator |
| `POST` | `/api/simulator/stop` | Pause transaction simulator |
| `WebSocket` | `/ws` | Real-time updates (stats, alerts, new shadows) |

---

## 📁 Project Structure

```
Shadow Supply Chain/
│
├── app.py                  # Main FastAPI server (2400+ lines)
│                           # Routes, WebSocket, authentication, simulator
│
├── ai_copilot.py           # AI Copilot module
│                           # Groq chat + Cohere summarization
│
├── ai_module.py            # Core AI/ML module
│                           # Isolation Forest, feature engineering, NLP
│
├── database.py             # SQLAlchemy ORM models (11 tables)
│                           # Database initialization and seeding
│
├── detection.py            # Shadow Detection Engine
│                           # PO matching, scoring, vendor trust updates
│
├── generate_data.py        # Synthetic dataset generator
│                           # 50+ transactions, 21 vendors, 18 POs
│
├── production_data.py      # Real-world SF infrastructure scenarios
│                           # Production-grade test data
│
├── pdf_generator.py        # PDF report generation engine
│                           # Executive summaries, styled tables
│
├── requirements.txt        # Python dependencies
│
├── shadow_supply.db        # SQLite database (auto-created)
│
├── static/
│   ├── index.html          # Main dashboard (SPA)
│   ├── login.html          # Authentication page
│   ├── styles.css          # "Kinetic Ledger" design system
│   ├── app.js              # Frontend logic (1700+ lines)
│   └── downloads/          # Generated PDF/CSV exports
│
└── data/
    ├── financial_transactions.csv
    ├── procurement_records.csv
    ├── vendors.csv
    ├── inventory.csv
    └── maintenance_logs.csv
```

---

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.10 or higher** installed on your system
- **Internet connection** (for AI API calls to Groq and Cohere)

### Step 1: Clone / Navigate to Project

```bash
cd "Shadow Supply Chain"
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | Latest | Web framework |
| `uvicorn` | Latest | ASGI server |
| `sqlalchemy` | Latest | Database ORM |
| `pandas` | Latest | Data processing |
| `scikit-learn` | Latest | ML anomaly detection |
| `groq` | Latest | Groq LLM client |
| `cohere` | Latest | Cohere LLM client |
| `fpdf2` | Latest | PDF generation |
| `openpyxl` | Latest | Excel export |
| `httpx` | Latest | HTTP client |
| `websockets` | Latest | Real-time communication |
| `python-multipart` | Latest | Form data parsing |
| `matplotlib` | Latest | Chart rendering for PDFs |

### Step 3: Generate Dataset (First Time Only)

```bash
python generate_data.py
```

This creates `data/` folder with CSV files simulating ERP data extraction.

### Step 4: Start the Server

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Open Dashboard

Open your browser and navigate to:
```
http://localhost:8000
```

---

## ▶️ Running the Application

```bash
# Start the server
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# The dashboard is available at:
# http://localhost:8000
```

On startup, the system automatically:
1. ✅ Initializes the SQLite database
2. ✅ Loads seed data (vendors, transactions, POs, inventory)
3. ✅ Runs the detection engine (flags shadow purchases)
4. ✅ Starts the real-time transaction simulator
5. ✅ Initializes Groq and Cohere AI clients

---

## 🔑 Default Credentials

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `nexus2026` |

> The system uses session-based cookie authentication. After login, you're redirected to the main dashboard.

---

## 🔐 API Keys Configuration

The project uses two AI providers. API keys are configured in `ai_copilot.py`:

### Groq (Fast LLM Inference)
```
Provider:   Groq Cloud
Model:      llama-3.3-70b-versatile (Meta's LLaMA 3.3)
Endpoint:   https://api.groq.com/openai/v1/chat/completions
API Key:    Set via GROQ_API_KEY environment variable (see .env.example)
Purpose:    Conversational AI chat, deep shadow analysis
Speed:      ~200ms inference (fastest LLM inference available)
```

### Cohere (Semantic AI)
```
Provider:   Cohere
Model:      command-a-03-2025
Endpoint:   https://api.cohere.com/v2/chat
API Key:    Set via COHERE_API_KEY environment variable (see .env.example)
Purpose:    Risk summarization, vendor insights, risk classification
```

### How to Update API Keys

Edit `ai_copilot.py` lines 19–20:

```python
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your-groq-key-here")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "your-cohere-key-here")
```

Or set environment variables (recommended for production):

```bash
set GROQ_API_KEY=your_groq_api_key_here
set COHERE_API_KEY=your_cohere_api_key_here
```

### Verifying AI Connectivity

After starting the server, visit:
```
http://localhost:8000/api/ai/health
```

Expected response when both are working:
```json
{
  "groq": { "status": "connected", "model": "llama-3.3-70b-versatile" },
  "cohere": { "status": "connected", "model": "command-a-03-2025" }
}
```

---

## 🖥️ Screenshots & Dashboard

### Dashboard Overview
The main dashboard features:
- **4 Stat Cards** — Financial Exposure, Integrity Variance (shadow rate), Detection Quality, Inventory Health
- **4 Interactive Charts** — Risk Trend (line), Shadow vs Matched (doughnut), Department Risk (horizontal bar), Category Distribution (polar area)
- **Live Activity Feed** — Real-time WebSocket-powered event stream
- **Urgent Actions Panel** — Top 5 critical items needing immediate review
- **Trend Insights** — Week-over-week shadow activity analysis

### Navigation Tabs
| Tab | What It Shows |
|-----|--------------|
| **Overview** | Dashboard with stats, charts, live feed, urgent actions |
| **Priority Queue** | AI-ranked shadows sorted by risk severity |
| **Telemetric Alerts** | Shadow purchase detections with approve/review/reject actions |
| **Transactions** | Full financial transaction ledger with shadow flags |
| **Procurement** | Approved purchase orders from ERP |
| **Vendors & Risk** | Vendor registry with trust scores and risk levels |
| **Inventory** | Current stock levels, reorder alerts |
| **Audit Trail** | System action log for compliance |

### AI Copilot Panel
- Floating button with **pulsing animation** in the bottom-right corner
- **Glassmorphic chat panel** with message bubbles and markdown formatting
- **Provider status indicators** (green dot = Groq connected, blue dot = Cohere connected)
- **Typing animation** while AI processes your query
- **Quick action buttons** for health check and risk summary

---

## 🔮 Future Enhancements

- [ ] **Role-Based Access Control** — Admin, Analyst, Auditor roles with different permissions
- [ ] **Email/Slack Alerts** — Automated notifications for critical shadow detections
- [ ] **PostgreSQL Migration** — Scale from SQLite to production-grade database
- [ ] **Historical ML Retraining** — Periodic model retraining with human feedback data
- [ ] **Supplier Portal** — Vendor self-service portal for compliance documentation
- [ ] **Multi-Currency Support** — Global procurement with exchange rate handling
- [ ] **Docker Deployment** — Containerized deployment for cloud environments

---

## 👥 Team

Built as part of an enterprise supply chain intelligence project.

---

<p align="center">
  <strong>Shadow Supply Chain Detection System v3.0</strong><br/>
  <em>Protecting procurement integrity through AI-powered intelligence</em>
</p>
