import asyncio
import zipfile
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pman.config import settings
from pman.editor import EditorManager
from pman.github import GitHubClient
from pman.models import Base, ProjectStatus
from pman.ollama import OllamaClient
from pman.orchestrator import FeedbackOrchestrator
from pman.repository import ProjectRepository
from pman.templates import TemplateGenerator
from pman.validator import ProjectValidator

app = typer.Typer(name="pman", help="SMOT Project Manager CLI")
console = Console()

plan_app = typer.Typer(name="plan", help="Project plan management")
app.add_typer(plan_app)


def _get_db_session():
    engine = create_engine(f"sqlite:///{settings.db_path}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    return session_factory()


@plan_app.command()
def new(name: str):
    """Create a new project plan."""
    session = _get_db_session()
    repo = ProjectRepository(session)
    project = repo.create_project(name)

    template = TemplateGenerator()
    content = template.generate(name)

    editor = EditorManager()
    result = editor.open_editor(content, name)

    if result.strip():
        editor.save_snapshot(result, name, 1)
        console.print(f"[green]Project '{name}' created (ID: {project.id})[/]")
    else:
        console.print("[yellow]Empty project — nothing saved[/]")


@plan_app.command()
def continue_(project_id: int = typer.Argument(..., help="Project ID to continue")):
    """Continue editing an existing project plan."""
    session = _get_db_session()
    repo = ProjectRepository(session)
    project = repo.get_project(project_id)

    if not project:
        console.print(f"[red]Project {project_id} not found[/]")
        raise typer.Exit(1)

    editor = EditorManager()
    content = editor.get_latest_content(project.name) or ""

    orchestrator = FeedbackOrchestrator()
    result = orchestrator.run_loop(project.name, initial_content=content)

    console.print(f"[green]Loop completed in {result.iterations} iterations[/]")
    if result.completed:
        console.print("[green]Project marked as done[/]")


@plan_app.command()
def status(
    project_id: int = typer.Argument(..., help="Project ID to check"),
    force_complete: bool = typer.Option(
        False, "--force-complete", help="Override and mark as complete",
    ),
):
    """Check project status."""
    session = _get_db_session()
    repo = ProjectRepository(session)
    project = repo.get_project(project_id)

    if not project:
        console.print(f"[red]Project {project_id} not found[/]")
        raise typer.Exit(1)

    if force_complete:
        repo.update_project_status(project_id, ProjectStatus.DONE)
        console.print(f"[green]Project {project_id} force-completed[/]")
        return

    editor = EditorManager()
    content = editor.get_latest_content(project.name) or ""
    validator = ProjectValidator()
    report = validator.check_completeness(content)

    console.print(f"[bold]Project: {project.name}[/]")
    console.print(f"Status: {project.status.value}")
    console.print(f"Completeness: {report.overall_score}%")
    if report.missing_sections:
        console.print(f"[yellow]Missing: {', '.join(report.missing_sections)}[/]")
    if report.yaml_errors:
        console.print(f"[red]Errors: {len(report.yaml_errors)}[/]")


@plan_app.command()
def export(
    project_id: int = typer.Argument(..., help="Project ID to export"),
    populate_db: bool = typer.Option(False, "--populate-db", help="Populate execution tables"),
):
    """Export project plan to markdown."""
    session = _get_db_session()
    repo = ProjectRepository(session)
    project = repo.get_project(project_id)

    if not project:
        console.print(f"[red]Project {project_id} not found[/]")
        raise typer.Exit(1)

    editor = EditorManager()
    content = editor.get_latest_content(project.name) or ""

    export_path = Path(settings.projects_dir) / project.name / "plan_export.md"
    export_path.write_text(content, encoding="utf-8")
    console.print(f"[green]Exported to {export_path}[/]")

    if populate_db:
        validator = ProjectValidator()
        blocks = validator.parse_yaml_blocks(content)

        wbs_data = blocks.get("wbs", {})
        for task in wbs_data.get("wbs", []):
            repo.create_wbs_task(
                project_id, task.get("id", ""), task.get("name", ""),
                duration_days=task.get("duration_days"),
                dependencies=str(task.get("dependencies", [])),
            )

        risks_data = blocks.get("risks", {})
        for risk in risks_data.get("risks", []):
            repo.create_risk(
                project_id, risk.get("description", ""),
                probability=risk.get("probability", "medium"),
                impact=risk.get("impact", "medium"),
                mitigation=risk.get("mitigation", ""),
                owner=risk.get("owner", ""),
            )

        console.print("[green]Populated execution tables[/]")


@plan_app.command("list")
def list_projects():
    """List all projects."""
    session = _get_db_session()
    repo = ProjectRepository(session)
    projects = repo.list_projects()

    table = Table(title="Projects", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Status", style="bold")
    table.add_column("Created", style="dim")

    for p in projects:
        table.add_row(str(p.id), p.name, p.status.value, str(p.created_at))

    console.print(table)


@app.command()
def backup(
    dest: str = typer.Option(".", "--dest", help="Destination directory"),
    restore: str = typer.Option(None, "--restore", help="Restore from archive"),
):
    """Backup or restore workspace."""
    pman_dir = Path.home() / ".pman"

    if restore:
        archive = Path(restore)
        if not archive.exists():
            console.print(f"[red]Archive not found: {restore}[/]")
            raise typer.Exit(1)

        if pman_dir.exists():
            console.print(f"[yellow]This will overwrite {pman_dir}[/]")
            if not typer.confirm("Continue?"):
                raise typer.Abort()

        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(Path.home())
        console.print(f"[green]Restored from {restore}[/]")
        return

    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = dest_path / f"pman-backup-{timestamp}.zip"

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in pman_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(Path.home())
                if ".env" in str(arcname):
                    zf.writestr(str(arcname), "# API keys sanitized\n")
                else:
                    zf.write(file_path, arcname)

    console.print(f"[green]Backup created: {archive_path}[/]")


@app.command()
def system_status():
    """Stato di tutti i servizi."""
    console.print("\n[bold cyan]SMOT-PMANAGER Status[/]\n")

    table = Table(title="Servizi", show_header=True, header_style="bold magenta")
    table.add_column("Servizio", style="cyan")
    table.add_column("URL/Path", style="green")
    table.add_column("Stato", style="bold")

    table.add_row("Ollama", settings.ollama_host, "[green]ONLINE[/]")
    gh_status = "[green]CONFIGURATO[/]" if settings.github_token else "[red]NO TOKEN[/]"
    table.add_row("GitHub API", settings.github_api_url, gh_status)
    table.add_row("SQLite", settings.db_path, "[green]OK[/]")
    table.add_row("Redis", settings.redis_url, "[yellow]NON VERIFICATO[/]")

    console.print(table)


@app.command()
def models():
    """Lista modelli Ollama disponibili."""
    client = OllamaClient()
    try:
        available = client.list_models()
        console.print("\n[bold cyan]Modelli Ollama disponibili:[/]")
        for m in available:
            marker = " 👈 default" if m == settings.ollama_model else ""
            console.print(f"  • [green]{m}[/]{marker}")
    except Exception as e:
        console.print(f"[red]Errore: {e}[/]")


@app.command()
def repos():
    """Lista repo GitHub tracciate."""
    async def _list():
        client = GitHubClient()
        try:
            data = await client.get_repos()
            console.print(f"\n[bold cyan]Repo trovati: {len(data)}[/]\n")
            for r in data[:10]:
                private = "🔒" if r.get("private") else "🌐"
                desc = r.get('description', 'N/A')
                console.print(f"  {private} [green]{r['full_name']}[/] — {desc}")
        except Exception as e:
            console.print(f"[red]Errore: {e}[/]")

    asyncio.run(_list())


@app.command()
def ask(prompt: str):
    """Chiedi qualcosa al modello Ollama."""
    client = OllamaClient()
    console.print(f"\n[bold cyan]🤖 {settings.ollama_model}:[/]\n")
    try:
        resp = client.generate(prompt=prompt, stream=False)
        console.print(resp.get("response", ""))
        eval_count = resp.get("eval_count", 0)
        eval_dur = resp.get("eval_duration", 1) / 1e9
        tps = eval_count / eval_dur if eval_dur > 0 else 0
        console.print(f"\n[dim][{eval_count} tok · {tps:.1f} tok/s][/]")
    except Exception as e:
        console.print(f"[red]Errore: {e}[/]")


def main():
    app()
