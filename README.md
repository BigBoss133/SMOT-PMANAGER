# SMOT-PMANAGER

[![CI](https://github.com/BigBoss133/SMOT-PMANAGER/actions/workflows/test.yml/badge.svg)](https://github.com/BigBoss133/SMOT-PMANAGER/actions/workflows/test.yml)

> **SMOT Project Manager** — AI-driven project orchestration for the SMOT ecosystem.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/BigBoss133/SMOT-PMANAGER.git
cd SMOT-PMANAGER

# 2. Create venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Install
pip install -e ".[dev]"

# 4. Configure
mv .env.example .env
# edit PMAN_GITHUB_TOKEN, PMAN_OLLAMA_HOST, etc.

# 5. Start API
uvicorn pman.api:app --reload

# 6. Use CLI
pman status
pman models
pman repos
pman ask "Spiega l'architettura"
```

---

## Project Plan Workflow

Create, iterate, and export project plans with AI feedback.

```bash
# Create a new project and start the feedback loop
pman plan new "My Project"

# Continue working on an existing project
pman plan continue 1

# Check a specific section with AI + RAG textbook analysis
pman plan check 1 --section "Risk Analysis"

# Check project status and completeness
pman plan status 1

# Force mark as complete
pman plan status 1 --force-complete

# List all projects
pman plan list
```

---

## Export & Bundle

Export project plans and generate deliverables for stakeholders.

```bash
# Export plan to Markdown
pman plan export 1

# Export + generate Excel workbook + Sponsor email
pman plan export 1 --bundle

# Export as JSON for the frontend dashboard
pman plan export 1 --json

# Combine: bundle + JSON
pman plan export 1 --bundle --json

# Export and populate execution tables (WBS, Risks in DB)
pman plan export 1 --populate-db
```

### Bundle Output

With `--bundle`, the following files are created in the project directory:

- `plan_export.md` — Full project plan
- `project_artifacts.xlsx` — Excel workbook with sheets: WBS, RACI, Risks, Budget
- `sponsor_email.txt` — Pre-filled email with key metrics (budget, tasks, top risk)

### Frontend Dashboard

A React dashboard renders the JSON output interactively.

```bash
cd frontend
npm install
npm run dev       # Development
npm run build     # Static build in dist/
```

Open the dashboard, load a JSON file (or paste from `--json` output), and view:
- WBS table with durations and dependencies
- RACI matrix
- Risk register with color-coded probability/impact
- Budget breakdown with progress bars

Print to PDF directly from the browser.

---

## Backup & Restore

```bash
# Backup workspace to zip
pman backup --dest ~/Backups

# Restore from archive
pman backup --restore ~/Backups/pman-backup-20260101-120000.zip
```

---

## Architecture

Vedi `projects/SMOT-PMANAGER.md` nel vault `shared-brain`.

---

## Modules

| Modulo | Scopo |
|--------|-------|
| `pman.config` | Pydantic settings |
| `pman.models` | SQLAlchemy ORM (async) |
| `pman.api` | FastAPI REST |
| `pman.cli` | Typer CLI |
| `pman.orchestrator` | AI feedback loop with RAG |
| `pman.rag` | RAG pipeline with ChromaDB |
| `pman.validator` | YAML block parsing & completeness check |
| `pman.bundle` | Excel + email generator |
| `pman.editor` | Cross-OS editor + session recovery |
| `pman.ai_providers` | Async AI providers (Ollama/OpenAI) with circuit breaker |

---

## API Endpoints

| Metodo | Path | Descrizione |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/projects` | Lista progetti |
| POST | `/api/v1/sync/github` | Sync GitHub |
| GET | `/api/v1/tasks` | Lista task |
| POST | `/api/v1/tasks/analyze` | Analizza codice |
| GET | `/api/v1/agents/status` | Stato Ollama |

---

## License

MIT
