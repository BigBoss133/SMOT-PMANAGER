# SMOT-PMANAGER — Guida Completa allo Sviluppo

> **Versione**: 1.0 — Maggio 2026
> **Piano di riferimento**: `docs/PLAN.md` (24 task, 4 ondate)

---

## 📋 Indice

1. [Panoramica del Progetto](#1-panoramica-del-progetto)
2. [Architettura](#2-architettura)
3. [Setup dell'Ambiente](#3-setup-dellambiente)
4. [Workflow di Sviluppo (TDD)](#4-workflow-di-sviluppo-tdd)
5. [Guida per Ondata](#5-guida-per-ondata)
6. [Guida per Modulo](#6-guida-per-modulo)
7. [Strategia di Test](#7-strategia-di-test)
8. [Gestione Errori](#8-gestione-errori)
9. [Integrazione AI](#9-integrazione-ai)
10. [FAQ e Troubleshooting](#10-faq-e-troubleshooting)

---

## 1. Panoramica del Progetto

### Cos'è SMOT-PMANAGER?

Un tool CLI che guida l'utente nella creazione di un Project Plan professionale usando l'AI. Il flusso:

```
pman plan new --name "MioProgetto"
    ↓
Apre $EDITOR con template markdown
    ↓
Utente scrive le sezioni del progetto
    ↓
Salva (CTRL+S) → AI analizza con RAG sulla dispensa
    ↓
AI fornisce feedback: cosa manca, suggerimenti
    ↓
Loop: modifica → salva → feedback (max 10 iterazioni)
    ↓
Utente scrive --done → Esporta Project Plan finale
```

### Deliverable Finali

Il Project Plan contiene 5 sezioni obbligatorie:
1. **Project Charter** — obiettivi, scope, vincoli, assunzioni
2. **Stakeholder Analysis + RACI** — chi è coinvolto e con che ruolo
3. **Work Breakdown Structure + Schedule** — cosa fare e quando
4. **Risk Analysis** — matrice probabilità/impatto
5. **Budget + Cost Estimation** — stima costi

### Knowledge Base

L'AI usa come riferimento la dispensa universitaria **"Google Project Management Professional Certificate"** (134 pagine, 39 capitoli), indicizzata tramite RAG (Retrieval Augmented Generation).

---

## 2. Architettura

```
SMOT-PMANAGER/
├── src/pman/
│   ├── __init__.py          # Package, versione 0.1.0
│   ├── main.py              # Entry point uvicorn (API)
│   ├── config.py            # Pydantic BaseSettings [ESISTENTE]
│   ├── models.py            # SQLAlchemy ORM [ESISTENTE]
│   ├── database.py          # [NUOVO] Async session + init_db
│   ├── repository.py        # [NUOVO] Project CRUD
│   ├── pdf_extractor.py     # [NUOVO] Estrazione testo PDF
│   ├── embedder.py          # [NUOVO] Chunking + embedding
│   ├── vector_store.py      # [NUOVO] ChromaDB integration
│   ├── rag.py               # [NUOVO] RAG query pipeline
│   ├── ai_providers.py      # [NUOVO] AI factory (Ollama + OpenAI)
│   ├── feedback.py          # [NUOVO] Generatore feedback AI
│   ├── validator.py         # [NUOVO] Parser + completezza
│   ├── templates.py         # [NUOVO] Generatore template
│   ├── editor.py            # [NUOVO] Editor + temp file
│   ├── orchestrator.py      # [NUOVO] Loop orchestratore
│   ├── errors.py            # [NUOVO] Eccezioni custom
│   ├── cli.py               # Typer CLI [ESTESO]
│   ├── commands/
│   │   └── plan.py          # [NUOVO] Comandi plan
│   ├── github.py            # GitHub API client [ESISTENTE]
│   └── ollama.py            # Ollama client [DA RENDERE ASYNC]
├── templates/               # [NUOVO] Template markdown
│   └── project_plan.md
├── tests/
│   ├── conftest.py          # [NUOVO] Fixtures
│   ├── test_config.py       # [NUOVO]
│   ├── test_models.py       # [NUOVO]
│   ├── test_pdf_extractor.py
│   ├── test_embedder.py
│   ├── test_vector_store.py
│   ├── test_rag.py
│   ├── test_ai_providers.py
│   ├── test_feedback.py
│   ├── test_validator.py
│   ├── test_templates.py
│   ├── test_editor.py
│   ├── test_orchestrator.py
│   ├── test_repository.py
│   ├── test_errors.py
│   ├── test_cli_plan.py
│   └── test_e2e.py
├── pyproject.toml
├── .env.example
└── README.md
```

### Diagramma dei Componenti

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   CLI (Typer)│────▶│ Orchestrator │────▶│  Validator   │
│  plan new    │     │  (loop)      │     │  (parser)    │
│  plan status │     └──────┬───────┘     └──────────────┘
└─────────────┘            │
                           ▼
                    ┌──────────────┐     ┌──────────────┐
                    │   Feedback   │────▶│ AI Provider  │
                    │   Generator  │     │ (Ollama/API) │
                    └──────┬───────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌──────────────┐
                    │     RAG      │────▶│  VectorStore │
                    │   Pipeline   │     │  (ChromaDB)  │
                    └──────┬───────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Embedder   │
                    │ (nomic/OpenAI│
                    └──────────────┘

┌──────────────┐     ┌──────────────┐
│   Editor     │     │  Repository  │
│   Manager    │     │  (SQLite)    │
└──────────────┘     └──────────────┘
```

---

## 3. Setup dell'Ambiente

### Prerequisiti

```bash
# Python 3.12+
python --version  # Deve essere ≥ 3.12

# Ollama (per AI locale)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text   # Embedding model
ollama pull llama3              # LLM model

# pdftotext (per estrazione PDF)
sudo apt-get install poppler-utils  # Ubuntu/Debian
brew install poppler                 # macOS

# Git
git --version
```

### Installazione

```bash
# Clona il repo
git clone https://github.com/BigBoss133/SMOT-PMANAGER.git
cd SMOT-PMANAGER

# Crea virtual environment
python -m venv .venv
source .venv/bin/activate

# Installa dipendenze
pip install -e ".[dev]"

# Configura ambiente
cp .env.example .env
# Modifica .env con le tue configurazioni
```

### Configurazione `.env`

```bash
# === AI Provider ===
AI_PROVIDER=ollama                    # ollama | openai
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=llama3
OPENAI_API_KEY=sk-...                 # Opzionale

# === RAG ===
RAG_PDF_PATH=/home/user/Scrivania/SmotPmanager/Google_PM_Dispensa_Universitaria_LIBRO.pdf
RAG_CHUNK_SIZE=512
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=5

# === ChromaDB ===
CHROMA_PATH=~/.pman/chromadb
CHROMA_COLLECTION=pm_textbook

# === Database ===
DB_PATH=~/.pman/pman.db

# === Projects ===
PROJECTS_DIR=~/.pman/projects
```

### Verifica Setup

```bash
pman status
# Output atteso:
# ┌──────────┬─────────┐
# │ Servizio │ Stato   │
# ├──────────┼─────────┤
# │ Ollama   │ ONLINE  │
# │ GitHub   │ ONLINE  │
# │ SQLite   │ ONLINE  │
# └──────────┴─────────┘
```

---

## 4. Workflow di Sviluppo (TDD)

### Ciclo RED-GREEN-REFACTOR

```bash
# 1. RED — Scrivi il test che fallisce
# tests/test_nuovo_modulo.py

# 2. GREEN — Implementa il minimo
# src/pman/nuovo_modulo.py

# 3. REFACTOR — Migliora senza rompere

# 4. Verifica coverage
pytest tests/test_nuovo_modulo.py -v --cov=src/pman.nuovo_modulo --cov-report=term
```

### Struttura dei Test

```python
# tests/test_nuovo_modulo.py
import pytest
from pman.nuovo_modulo import NuovaClasse

class TestNuovaClasse:
    """Test per NuovaClasse."""

    def test_happy_path(self):
        """Funzionamento base con input valido."""
        result = NuovaClasse().metodo("input valido")
        assert result is not None

    def test_edge_case_empty(self):
        """Input vuoto deve lanciare errore."""
        with pytest.raises(ValueError, match="non può essere vuoto"):
            NuovaClasse().metodo("")

    def test_edge_case_None(self):
        """Input None deve lanciare TypeError."""
        with pytest.raises(TypeError):
            NuovaClasse().metodo(None)
```

### Convenzioni
- **Naming**: `test_<modulo>.py`, `Test<Classe>`, `test_<scenario>`
- **Docstring**: ogni test spiega cosa verifica
- **AAA**: Arrange → Act → Assert
- **Un test = un comportamento**
- **Mock esterni**: Ollama, OpenAI, file system

---

## 5. Guida per Ondata

### Ondata 1 (T1-T7): Fondazione — 7 task in parallelo

**Obiettivo**: Infrastruttura pronta.

| Task | Modulo | Descrizione |
|------|--------|-------------|
| T1 | tests/ | Test infrastructure (conftest, fixtures) |
| T2 | pdf_extractor.py | Estrazione testo PDF via pdftotext |
| T3 | embedder.py | Chunking 512 token + embedding |
| T4 | vector_store.py | ChromaDB PersistentClient |
| T5 | config.py | Nuovi settings RAG + AI |
| T6 | templates.py | Template markdown 5 sezioni |
| T7 | editor.py | Editor $EDITOR + temp file |

**Checkpoint**:
```bash
pytest tests/ -v --cov=src/pman --ignore=tests/test_e2e.py
```

### Ondata 2 (T8-T14): Core Logic

| Task | Modulo | Dipende da |
|------|--------|------------|
| T8 | validator.py | T1, T6 |
| T9 | rag.py | T4, T3 |
| T10 | ai_providers.py + feedback.py | T5, T9 |
| T11 | orchestrator.py | T8, T9, T10, T14 |
| T12 | database.py + repository.py | T1 |
| T13 | ai_providers.py (cloud) | T5 |
| T14 | errors.py | — |

**Checkpoint**:
```bash
pytest tests/test_orchestrator.py tests/test_feedback.py tests/test_rag.py -v
```

### Ondata 3 (T15-T20): CLI Commands

| Task | Comando | Dipende da |
|------|---------|------------|
| T15 | `plan new` | T6, T7, T11, T12, T13 |
| T16 | `plan continue` | T11, T12, T14 |
| T17 | `plan status` | T8, T12 |
| T18 | `plan export` | T12 |
| T19 | `plan list` | T12 |
| T20 | CLI refactoring | T15-T19 |

**Checkpoint**:
```bash
pman plan --help
# Output: new, continue, status, export, list
```

### Ondata 4 (T21-T24): Integration & Polish

| Task | Descrizione |
|------|-------------|
| T21 | E2E tests (new→edit→export) |
| T22 | Session recovery (crash → ripristino) |
| T23 | Performance (caching, lazy loading) |
| T24 | Refactoring (async ollama, fix bugs, clean stubs) |

**Checkpoint Finale**:
```bash
pytest tests/ -v --cov=src/pman --cov-fail-under=80
ruff check src/pman/
# 0 errori, coverage ≥ 80%
```

---

## 6. Guida per Modulo

### 6.1 `pdf_extractor.py` — Estrazione Testo PDF

```python
from dataclasses import dataclass
import subprocess, re
from pathlib import Path

@dataclass
class Chapter:
    number: int
    title: str
    content: str

class PDFExtractor:
    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)

    def extract_text(self) -> str:
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF non trovato: {self.pdf_path}")
        result = subprocess.run(
            ["pdftotext", str(self.pdf_path), "-"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"pdftotext error: {result.stderr}")
        if len(result.stdout) < 1000:
            raise ValueError("PDF potrebbe essere scansionato (testo insufficiente)")
        return result.stdout

    def extract_chapters(self) -> list[Chapter]:
        text = self.extract_text()
        pattern = r"CAPITOLO\s+(\d+):\s*([^\n]+)"
        matches = list(re.finditer(pattern, text))
        chapters = []
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            chapters.append(Chapter(
                number=int(m.group(1)),
                title=m.group(2).strip(),
                content=text[start:end].strip()
            ))
        return chapters
```

### 6.2 `validator.py` — Parser + Completezza

```python
from dataclasses import dataclass, field

REQUIRED_SECTIONS = [
    "Project Charter", "Stakeholder Analysis",
    "Work Breakdown Structure", "Risk Analysis", "Budget"
]

@dataclass
class SectionStatus:
    present: bool
    word_count: int
    has_content: bool  # > 50 parole

@dataclass
class CompletenessReport:
    sezioni: dict[str, SectionStatus]
    overall_score: float  # 0-100
    missing_sections: list[str] = field(default_factory=list)

class ProjectValidator:
    MIN_WORDS = 50

    def parse_sections(self, content: str) -> dict[str, str]:
        sections = {}
        current = None
        lines_buf = []
        for line in content.split("\n"):
            if line.startswith("## "):
                if current:
                    sections[current] = "\n".join(lines_buf)
                current = line[3:].strip()
                lines_buf = []
            elif current:
                lines_buf.append(line)
        if current:
            sections[current] = "\n".join(lines_buf)
        return sections

    def check_completeness(self, sections: dict[str, str]) -> CompletenessReport:
        report = {}
        missing = []
        for name in REQUIRED_SECTIONS:
            content = sections.get(name, "")
            wc = len(content.split())
            report[name] = SectionStatus(
                present=name in sections,
                word_count=wc,
                has_content=wc >= self.MIN_WORDS
            )
            if not report[name].has_content:
                missing.append(name)
        complete = sum(1 for s in report.values() if s.has_content)
        return CompletenessReport(
            sezioni=report,
            overall_score=(complete / len(REQUIRED_SECTIONS)) * 100,
            missing_sections=missing
        )
```

### 6.3 `orchestrator.py` — Loop Orchestratore

```python
class FeedbackLoop:
    MAX_ITERATIONS = 10

    def __init__(self, editor, validator, rag, feedback_gen, repository):
        self.editor = editor
        self.validator = validator
        self.rag = rag
        self.feedback_gen = feedback_gen
        self.repository = repository

    async def run(self, project_name: str) -> str:
        iteration = 0
        content = ""
        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            content = self.editor.open_editor(content or self._template(), project_name)
            if "## STATUS: COMPLETO" in content or "--done" in content:
                break
            sections = self.validator.parse_sections(content)
            report = self.validator.check_completeness(sections)
            if report.overall_score >= 100:
                if input("Completo 100%. Finalizzare? [Y/n] ").lower() != "n":
                    break
            ctx = await self.rag.query_sections(report.missing_sections)
            feedback = await self.feedback_gen.generate(report, ctx)
            self._display(feedback, report)
            self.editor.save_snapshot(content, project_name, iteration)
        return content
```

### 6.4 `ai_providers.py` — Factory Pattern

```python
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "") -> str: ...

class OllamaProvider(AIProvider):
    async def generate(self, prompt, system_prompt=""):
        # Usa httpx.AsyncClient per API Ollama
        ...

class OpenAIProvider(AIProvider):
    async def generate(self, prompt, system_prompt=""):
        # Usa httpx.AsyncClient per API OpenAI
        ...

class AIFactory:
    @staticmethod
    def create(settings) -> AIProvider:
        if settings.ai_provider == "openai":
            return OpenAIProvider(settings)
        return OllamaProvider(settings)
```

---

## 7. Strategia di Test

### Livelli

| Livello | Scope | Mock |
|---------|-------|------|
| **Unit** | Singole classi/funzioni | Esterni (Ollama, OpenAI, fs) |
| **Integration** | Collaborazione moduli | HTTP mock |
| **CLI** | Comandi Typer | Tutti i moduli |
| **E2E** | Flusso completo | Solo AI provider |

### Fixtures (`conftest.py`)

```python
import pytest, tempfile
from pathlib import Path

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def mock_ollama(httpx_mock):
    httpx_mock.add_response(
        url="http://localhost:11434/api/embeddings",
        json={"embedding": [0.1] * 768}
    )

@pytest.fixture
def mock_openai(httpx_mock):
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        json={"choices": [{"message": {"content": "Feedback test"}}]}
    )

@pytest.fixture
def sample_template():
    return "# Project Plan\n\n## Project Charter\nTest\n\n## Stakeholder Analysis\n...\n"
```

### Esecuzione

```bash
pytest tests/ -v                          # Tutti
pytest tests/ -v --ignore=tests/test_e2e.py  # Solo unit
pytest tests/ -v --cov=src/pman --cov-report=html
pytest tests/test_validator.py -v         # Modulo specifico
pytest tests/test_validator.py::TestProjectValidator::test_full_template -v
```

---

## 8. Gestione Errori

### Gerarchia

```python
class PMANError(Exception):
    def __init__(self, message: str, user_message: str = None):
        self.user_message = user_message or message
        super().__init__(message)

class EditorError(PMANError): ...
class AIError(PMANError): ...
class RAGError(PMANError): ...
class ConfigError(PMANError): ...
```

### Matrice di Degradazione

| Scenario | Azione | Messaggio |
|----------|--------|-----------|
| Ollama down | Tenta cloud | "Ollama KO, provo cloud..." |
| Cloud down | Feedback generico | "AI non disp. Feedback base." |
| PDF mancante | RAG off | "Dispensa non trovata. RAG off." |
| ChromaDB rotto | Reinizializza | "Reindicizzazione in corso..." |
| Editor crash | Recupera snapshot | "Crash. Ripristino ultimo snapshot." |
| Disco pieno | Errore fatale | "Spazio disco insufficiente." |

---

## 9. Integrazione AI

### Provider

| Provider | Embedding | LLM | Costo |
|----------|-----------|-----|-------|
| **Ollama** | `nomic-embed-text` | `llama3`, `mistral` | Gratuito |
| **OpenAI** | `text-embedding-3-small` | `gpt-4o-mini` | API |

### System Prompt (per feedback AI)

```
Sei un project manager esperto certificato Google PM.
Usa il contesto della dispensa per suggerire miglioramenti.

Regole:
1. Per ogni sezione mancante, 2-3 suggerimenti specifici
2. Cita il capitolo della dispensa (es. "Cap. 7 - Project Charter")
3. Sii costruttivo: COME completare, non solo COSA manca
4. Massimo 500 parole per feedback
```

---

## 10. FAQ e Troubleshooting

### Q: Come aggiungo un nuovo provider AI?
1. Aggiungi classe in `ai_providers.py`
2. Registra in `AIFactory.create()`
3. Aggiungi settings in `config.py`
4. Test in `test_ai_providers.py`

### Q: Come cambio il template?
Modifica `templates/project_plan.md`. Mantieni 5 sezioni con `## `.

### Q: Embedding lento?
Primo avvio: ~30-60s (processa PDF). Successivi: cache (<1s).

### Q: Come resetto tutto?
```bash
rm ~/.pman/pman.db
rm -rf ~/.pman/chromadb/
```

### Q: Come debuggo?
```bash
pman --verbose plan new --name "Debug"
PMAN_LOG_LEVEL=DEBUG pman plan new
pytest tests/test_x.py -vv --tb=long
```

### Q: Come contribuisco?
1. Fork → branch `feat/nome`
2. TDD: test → implementa → refactor
3. `pytest && ruff check .`
4. Commit: `feat(pman): descrizione`
5. Push → PR

---

## 📚 Riferimenti

- **Piano**: `docs/PLAN.md`
- **Dispensa**: `Scrivania/SmotPmanager/Google_PM_Dispensa_Universitaria_LIBRO.pdf`
- **Repo**: https://github.com/BigBoss133/SMOT-PMANAGER
- **ChromaDB**: https://docs.trychroma.com/
- **Typer**: https://typer.tiangolo.com/
- **Ollama**: https://github.com/ollama/ollama/blob/main/docs/api.md

---

*Guida generata dal piano di sviluppo SMOT-PMANAGER. Maggio 2026.*
