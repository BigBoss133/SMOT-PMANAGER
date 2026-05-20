# SMOT-PMANAGER

> **SMOT Project Manager** — AI-driven project orchestration for the SMOT ecosystem.

---

## Quick Start

```bash
# 1. Clona (gia' privato)
git clone https://github.com/BigBoss133/SMOT-PMANAGER.git
cd SMOT-PMANAGER

# 2. Crea venv
python3 -m venv .venv
source .venv/bin/activate

# 3. Installa
pip install -e ".[dev]"

# 4. Configura
mv .env.example .env
# modifica PMAN_GITHUB_TOKEN, se necessario

# 5. Avvia
uvicorn pman.api:app --reload

# 6. CLI
pman status
pman models
pman repos
pman ask "Spiega l'architettura"
```

---

## Architettura

Vedi `projects/SMOT-PMANAGER.md` nel vault `shared-brain`.

---

## Moduli

| Modulo | Scopo |
|--------|-------|
| `pman.config` | Pydantic settings |
| `pman.models` | SQLAlchemy ORM |
| `pman.api` | FastAPI REST |
| `pman.github` | GitHub REST client |
| `pman.ollama` | Ollama local LLM client |
| `pman.cli` | Typer CLI |

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
