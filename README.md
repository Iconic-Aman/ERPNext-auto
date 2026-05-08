# ERPNext-Auto 🤖

> **ERPNext as the Brain. LangGraph as the Hands. Zero human overhead.**

Autonomous CRM system that handles the full customer lifecycle — from the first WhatsApp message to final payment reconciliation — without human input.

Built with **LangGraph + LangChain** (agent orchestration) + **FastAPI** (webhook server) + **ERPNext** (ERP/database).

---

## What Gets Automated

| Phase | Replaces |
|---|---|
| Phase 1 – Acquisition | Sales exec qualifying leads & creating CRM records |
| Phase 2 – Execution | PM setting up projects & assigning tasks |
| Phase 3 – Billing | Accountant generating & sending invoices |
| Phase 4 – Reconciliation | Accountant verifying payment screenshots |

---

## Tech Stack

| Layer | Tool |
|---|---|
| ERP / Database | ERPNext (Docker) |
| Agent Orchestration | LangGraph |
| Agent Framework | LangChain |
| API Server | FastAPI + uvicorn |
| LLM | NVIDIA NIM (Llama 3.1) |
| Memory | LangGraph Checkpointer (SQLite / Redis) |
| HTTP Client | httpx (async) |
| WhatsApp | Meta WhatsApp Business API |
| Email | SMTP |

---

## Repo Structure

```
ERPNext-auto/
├── main.py                  # FastAPI app — webhook endpoints
├── config.py                # Env var loader (single source of truth)
├── checkpointer.py          # LangGraph SQLite/Redis checkpointer
├── agents/
│   ├── agent1_crm.py        # Graph 1: Conversation & Qualification (stateful)
│   ├── agent2_projects.py   # Graph 2: Deal Monitor & Project Setup
│   ├── agent3_billing.py    # Graph 3: Billing Agent
│   └── agent4_vision.py     # Graph 4: Vision Reconciliation
├── tools/
│   ├── erpnext.py           # httpx wrappers for ERPNext REST API
│   └── whatsapp.py          # WhatsApp send functions
├── state/
│   └── schemas.py           # TypedDict state schemas for all 4 graphs
├── .env                     # Secrets (gitignored)
├── .gitignore
└── requirements.txt
```

---

## Setup

```bash
# 1. Clone and enter repo
git clone <repo-url> && cd ERPNext-auto

# 2. Create virtual env
python -m venv venv && venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Fill in .env (copy from .env.example)

# 5. Run
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

For local WhatsApp webhook testing:
```bash
ngrok http 8000
```

---

## Design

Full system design → [`ERPNext-langgraph-design.md`](ERPNext-langgraph-design.md)
