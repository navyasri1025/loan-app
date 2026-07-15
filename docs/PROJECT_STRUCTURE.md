# Project Structure

This document outlines the codebase organization and layout.

---

## Codebase Map

```
Loan Application/
├── backend/                  # FastAPI + SQLAlchemy + LangGraph
│   ├── app/
│   │   ├── agents/           # LangGraph cooperative multi-agents
│   │   │   ├── intake_agent.py
│   │   │   ├── ocr_agent.py
│   │   │   ├── validation_agent.py
│   │   │   ├── policy_engine_agent.py
│   │   │   ├── decision_agent.py
│   │   │   ├── fairness_agent.py
│   │   │   ├── governance_agent.py
│   │   │   └── workflow.py   # StateGraph compilation & triggers
│   │   ├── core/             # Auth keys, logger, prompt protectors
│   │   ├── models/           # SQLAlchemy models
│   │   └── routers/          # HTTP Endpoint handlers
│   ├── uploads/              # PDF document stores
│   └── requirements.txt      # Backend Python dependencies
├── frontend/                 # React client
│   ├── src/
│   │   ├── components/       # Layouts, Route guards
│   │   ├── context/          # JWT Context
│   │   ├── pages/            # Role-specific dashboard consoles
│   │   └── services/         # API HTTP fetch helpers
│   └── package.json          # Frontend packages
└── docs/                     # Comprehensive Capstone documentation
```
