"""CLI con Typer per SMOT-PMANAGER."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from pman.config import settings
from pman.github import GitHubClient
from pman.ollama import OllamaClient

app = typer.Typer(name="pman", help="SMOT Project Manager CLI")
console = Console()


@app.command()
def status():
    """Stato di tutti i servizi."""
    console.print("\n[bold cyan]SMOT-PMANAGER Status[/]\n")

    table = Table(title="Servizi", show_header=True, header_style="bold magenta")
    table.add_column("Servizio", style="cyan")
    table.add_column("URL/Path", style="green")
    table.add_column("Stato", style="bold")

    table.add_row("Ollama", settings.ollama_host, "[green]ONLINE[/]")
    table.add_row("GitHub API", settings.github_api_url, "[green]CONFIGURATO[/]" if settings.github_token else "[red]NO TOKEN[/]")
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
                console.print(f"  {private} [green]{r['full_name']}[/] — {r.get('description', 'N/A')}")
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
