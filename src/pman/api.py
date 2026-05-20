"""API REST con FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from pman.config import settings
from pman.github import GitHubClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    yield


app = FastAPI(
    title="SMOT-PMANAGER",
    description="AI-driven project orchestration for the SMOT ecosystem",
    version=settings.version if hasattr(settings, "version") else "0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/v1/projects")
async def list_projects():
    """Lista progetti monitorati."""
    return {"projects": []}  # TODO: query DB


@app.post("/api/v1/sync/github")
async def sync_github():
    """Forza sync repository GitHub."""
    client = GitHubClient(token=settings.github_token)
    return {"status": "syncing", "token_set": bool(settings.github_token)}


@app.get("/api/v1/tasks")
async def list_tasks(status: str | None = None, project: str | None = None):
    """Lista task con filtri."""
    filters = {}
    if status:
        filters["status"] = status
    if project:
        filters["project"] = project
    return {"tasks": [], "filters": filters}


@app.post("/api/v1/tasks/analyze")
async def analyze_code():
    """Analizza codebase ed estrae task."""
    return {"status": "analyzing", "tasks_created": 0}


@app.post("/api/v1/report/velocity")
async def report_velocity(project_id: int):
    """Genera report velocity."""
    return {"report": "velocity_placeholder"}


@app.get("/api/v1/agents/status")
async def agent_status():
    """Stato connessione Ollama."""
    return {"ollama_host": settings.ollama_host, "model": settings.ollama_model}
