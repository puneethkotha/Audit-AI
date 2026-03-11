# AuditAI

**AuditAI** extracts structured compliance fields from unstructured clinical notes using an LLM, runs them through configurable rules, and returns a detailed audit report flagging billing and clinical compliance risks. Built for healthcare platforms that need automated documentation review.

## Quick start

```bash
# Clone and run
git clone https://github.com/puneethkotha/Audit-AI.git
cd Audit-AI

# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here

# Start all services
docker-compose up --build

# Seed default compliance rules (first run)
docker-compose exec backend python seed_rules.py
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Metrics**: http://localhost:8000/metrics

## GitHub Pages

The frontend deploys to GitHub Pages on each push to `main`. Enable it in your repository: Settings > Pages > Source: GitHub Actions. The static site runs at `https://puneethkotha.github.io/Audit-AI/`. For full audit functionality, run the backend locally or deploy it separately and set `VITE_API_URL` when building.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React     │────▶│   FastAPI    │────▶│   Claude    │
│  Frontend   │     │   Backend    │     │    API      │
└─────────────┘     └──────┬───────┘     └─────────────┘
                          │
           ┌──────────────┼──────────────┐
           ▼              ▼              ▼
    ┌────────────┐  ┌──────────┐  ┌──────────┐
    │ PostgreSQL │  │  Redis   │  │Prometheus │
    └────────────┘  └──────────┘  └──────────┘
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/audit` | Run compliance audit on a clinical note |
| GET | `/audit/{id}` | Retrieve audit result by ID |
| GET | `/rules` | List all compliance rules |
| POST | `/rules` | Create a new rule |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

## Sample request

```bash
curl -X POST http://localhost:8000/audit \
  -H "Content-Type: application/json" \
  -d '{"note_text": "Patient is a 67-year-old male presenting with chest pain. History of hypertension. Medications: metformin, lisinopril, oxycodone PRN. Vitals: BP 158/92. Admitted for observation."}'
```

## Tech stack

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

- **Backend**: Python, FastAPI, SQLAlchemy async, Anthropic Claude  
- **Frontend**: React, TypeScript, Tailwind CSS  
- **Data**: PostgreSQL, Redis (deduplication)  
- **Observability**: Prometheus metrics

## Project structure

```
auditai/
├── backend/           # FastAPI service
│   ├── main.py
│   ├── routers/       # audit, rules
│   ├── services/      # extractor, rule_engine, audit_service
│   ├── models/        # db, schemas
│   └── core/          # config, metrics, database
├── frontend/          # React app
└── docker-compose.yml
```

## License

MIT
