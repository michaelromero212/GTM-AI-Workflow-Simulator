# GTM AI Workflow Simulator

*Modeling how AI agents reduce friction across Sales, Customer Success, and Revenue Operations.*

GTM teams lose pipeline velocity to manual research, inconsistent deal inspection, and reactive post-sales workflows. This simulator demonstrates how AI agents can be deployed with governance, QA'd before rollout, measured against revenue KPIs, and iterated on using real field feedback — end-to-end, from intake to production.


## 📈 Revenue Impact (Simulated Environment)

| Metric | Result | How |
|--------|--------|-----|
| SDR Research Time | **~40% reduction** | Automated lead summarization replaces manual CRM + web research |
| AI Suggestion Acceptance | **68% → 82%** | Structured prompt iteration with QA gates and feedback logging |
| Hallucination / Rule Violations | **11% → 3%** | Governance constraints, escalation logic, and pre-deployment QA |
| CRM Data Completeness | **+15% improvement** | AI-generated structured call summaries with required field validation |

---

## 🔄 Where AI Intervenes in the Revenue Lifecycle

| Stage | AI Workflow | KPI |
|-------|------------|-----|
| **Pipeline Generation** | Lead Brief Generator — automated research, qualification signals, next-best-action | Research Time, Conversion Rate |
| **Deal Execution** | Risk Signal Classifier — stalled deal detection, missing stakeholder alerts, competitive flags | Slipped Deals %, Forecast Accuracy |
| **Onboarding & Adoption** | Usage Insight Summary — customer health scoring, adoption milestone tracking | Time-to-Value, Expansion Signals |
| **Renewal & Expansion** | Health Risk Flags + Next Best Action — churn prediction, upsell/cross-sell surfacing | Renewal Rate, NRR Impact |

---

## 🎯 What This Simulator Covers

- **Business Intent & Governance** — How AI agent behavior is defined, constrained, and audited
- **AI Agent Operations** — End-to-end agent implementation using LLMs (Hugging Face)
- **QA & Validation** — Pre-deployment testing, hallucination tracking, rule violation detection
- **KPIs & Analytics** — SQL-based metrics tied to revenue outcomes
- **Dashboards** — Operational health monitoring with interactive visualizations
- **Operational Diagnostics** — In-depth auditing and bottleneck analysis
- **A/B Testing** — Data-driven rollout decisions with statistical analysis
- **Enablement** — Rollout playbooks, training assets, and business reviews

## 🏗️ Project Structure

```
Databricks-AI-Agent-Operations-&-GTM-Ops-Simulator/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git exclusions
│
├── docs/                              # Business documentation
│   ├── business_intent.md            # Agent definition & governance
│   ├── kpis.md                       # KPI definitions
│   ├── rollout_plan.md               # Deployment strategy
│   └── enablement.md                 # User guidance
│
├── agent/                             # AI Agent implementation
│   ├── agent.py                      # Core agent logic
│   └── prompts.py                    # Prompt templates
│
├── qa/                                # Quality assurance
│   ├── test_cases.json               # Structured test cases
│   └── run_qa.py                     # QA test runner
│
├── data/                              # Data storage
│   ├── sample_agent_runs.csv         # Sample agent interaction data
│   └── uploaded_inputs/              # User-uploaded files
│
├── analytics/                         # Data analytics
│   ├── load_data.py                  # Data ingestion (DuckDB)
│   └── queries.sql                   # SQL queries for KPIs
│
├── dashboards/                        # Visualization
│   └── kpi_dashboard.ipynb           # Jupyter dashboard
│
├── experiments/                       # A/B testing
│   └── ab_test.md                    # Experiment documentation
│
├── reviews/                           # Business reviews
│   └── weekly_business_review.md     # Review template
│
└── webapp/                            # Web application
    ├── app.py                        # FastAPI application
    ├── templates/                    # Jinja2 templates
    │   ├── layout.html              # Shared layout with sidebar
    │   ├── index.html               # Overview page
    │   ├── dashboard.html           # KPI dashboard
    │   ├── upload.html              # Test agent page
    │   └── explorer.html            # Operational Diagnostics
    └── static/
        └── styles.css               # Premium CSS design system
```

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/michaelromero212/GTM-AI-Workflow-Simulator.git
cd GTM-AI-Workflow-Simulator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Hugging Face Token (Optional)

```bash
export HF_TOKEN="your_huggingface_token_here"
```

Get a free token from [Hugging Face](https://huggingface.co/settings/tokens). The agent works without a token using mock responses.

### 3. Run the Web Application

```bash
cd webapp
HF_TOKEN=your_token uvicorn app:app --host 0.0.0.0 --port 8000
```

Open your browser to: **http://localhost:8000**

## 📸 Screenshots

### Performance Overview (Home Page)
The landing page shows real-time KPIs, A/B test comparisons, lead source performance, and recent activity—all with interactive Chart.js visualizations.

![Home Page](docs/images/home_page.jpg)

### KPI Dashboard
Comprehensive metrics including Task Accuracy (92%), User Satisfaction (4.18/5), Resolution Time, and Error Rate. Interactive bar charts compare Agent A vs Agent B performance.

![KPI Dashboard](docs/images/dashboard_kpis.jpg)

### Operational Diagnostics
Audit the `agent_runs` data directly. Includes preset buttons for common analyses (Executive Summary, Failure Audit, etc.) and a full data catalog reference.

![Diagnostics Page](docs/images/sql_explorer.jpg)

### Test Agent
Upload lead data, deal notes, or sales inputs to test the AI agent. Select a task type and receive real LLM-powered analysis with feedback buttons.

![Upload Page](docs/images/upload_page.jpg)

### AI Agent Response
Real AI-generated analysis from the Llama-3.2 model. Includes Company Overview, Industry & Use Case Fit, Suggested Questions, and Recommended Next Steps.

![Agent Response](docs/images/agent_response.jpg)

## 🎯 Role Alignment: GTM Systems & AI Engineer

This project demonstrates core competencies for **GTM AI** roles:

| Competency | Demonstration |
|------------|---------------|
| **0→1 Delivery** | Took ambiguous GTM pain points and shipped working AI workflows end-to-end |
| **Intake & Prioritization** | Defined requirements, success metrics, and backlog prioritization in `docs/` |
| **Cross-Functional Partnership** | Designed for Sales, CS, Ops, and Analytics stakeholders |
| **Governance & Guardrails** | QA gates, escalation rules, access controls, auditability from day one |
| **A/B Testing & Iteration** | Data-driven rollout decisions with Agent A vs B comparison |
| **Enablement & Rollout** | Training assets, office hours templates, comms plans |
| **Measurable Outcomes** | Every workflow tied to a revenue KPI with tracking infrastructure |

## 🚀 Key Features

### 🤖 AI Agent
- Accepts GTM tasks: lead summaries, follow-up suggestions, deal risk signals
- Uses Hugging Face LLMs (Llama-3.2-3B-Instruct)
- Implements governance rules and escalation logic
- Falls back to mock responses without token

### 📉 Operational Diagnostics
- **Overview**: Quick KPI snapshot, A/B comparison charts, recent activity
- **Dashboard**: Detailed metrics, trends, task type breakdown
- **Diagnostics**: Auditing console with preset diagnostic templates
- **Live Updates**: Every test agent run updates the dashboards

### 🔬 Operational Auditing
Run diagnostic reports directly against the agent data:
```sql
SELECT lead_source, COUNT(*) as volume, 
       ROUND(AVG(CASE WHEN user_accepted THEN 1.0 ELSE 0.0 END) * 100, 1) as accuracy
FROM agent_runs 
GROUP BY lead_source
ORDER BY accuracy DESC
```

### 🧪 A/B Testing
- Real-time comparison of Agent A (control) vs Agent B (experimental)
- Visual charts showing accuracy, satisfaction, and error rates
- Decision recommendations based on success criteria
- Detailed analysis in `experiments/ab_test.md`

### ✅ QA & Validation
- Structured test cases in JSON
- Automated test runner
- Accuracy, hallucination, and rule violation tracking
- Results feed into analytics pipeline

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Python |
| Frontend | Jinja2 + Chart.js |
| Database | DuckDB (in-memory SQL) |
| LLM | Hugging Face Inference API |
| Styling | Custom CSS (Databricks-inspired) |
| Data Format | CSV with live appends |

## 🛡️ Governance & Compliance by Design

Governance is built into every workflow, not bolted on after deployment:

- **Agent Constraints & Guardrails** — No autonomous external communication, no unauthorized data access, no strategic decisions without human review ([business_intent.md](docs/business_intent.md))
- **Escalation & Abstention Rules** — Agent automatically defers to humans for high-risk scenarios, ambiguous situations, and sensitive topics
- **QA Gates** — Structured test cases with hallucination detection, rule violation tracking, and accuracy thresholds before any rollout
- **Auditability** — Every agent run logged with user acceptance, confidence score, error flags, and version tracking
- **Privacy & Data Controls** — No PII in analytics, anonymized user IDs, configurable data retention policies
- **A/B Test Guardrails** — Auto-disable triggers if error rate > 10% or satisfaction < 2.5

## 🔒 Security & Best Practices

- ✅ Secrets via environment variables (no credentials in code)
- ✅ Input validation and SQL injection prevention
- ✅ Virtual environment isolation
- ✅ Rate limiting and security headers
- ✅ Professional error handling

## 🧪 Running QA Tests

```bash
python qa/run_qa.py
```

## 📈 Viewing Analytics (CLI)

```bash
python analytics/load_data.py
```

This loads data into DuckDB and executes queries from `analytics/queries.sql`.

## 📝 Documentation

See the `docs/` directory for detailed documentation:

- **business_intent.md** - Agent definition, rules, and success criteria
- **kpis.md** - Metric definitions and tracking methodology
- **rollout_plan.md** - Phased deployment strategy
- **enablement.md** - User training and guidance
- **experiments/ab_test.md** - A/B test methodology and results

## 🤝 Contributing

This is a demonstration project. Feel free to fork and adapt for your own use cases.

## 📄 License

MIT License - See LICENSE file for details

---

**Built to demonstrate how AI workflows are shipped, governed, and measured inside revenue organizations.**

*Last Updated: February 2026*
