# SMOT-PMANAGER — CLI Project Manager con AI

## TL;DR

> **Quick Summary**: Estendere il repo SMOT-PMANAGER con un sistema CLI che apre un editor markdown, guida l'utente nella compilazione di un Project Plan, e usa AI (RAG su dispensa universitaria) per fornire feedback iterativo fino al completamento.
>
> **Deliverables**:
> - Pipeline RAG su dispensa 134pp (PyMuPDF → chunk metadata → embedding → ChromaDB)
> - Loop editor esterno + AI feedback (section-based, advisory mode, cross-OS)
> - 7 comandi CLI (`plan new/check/continue/status/export/list` + `backup`)
> - Supporto AI duale (Ollama locale con circuit breaker + API cloud)
> - CI/CD automatica con GitHub Actions
> - Project Plan in Markdown + blocchi YAML strutturati
>
> **Estimated Effort**: Large (26 task + 4 verification)
> **Parallel Execution**: YES — 4 waves
> **Critical Path**: T6 (template) → T11 (loop orchestrator) → T15 (CLI) → T21 (E2E) → T25 (backup) → F1-F4

---

## Context

### Original Request
L'utente ha una dispensa universitaria di 134 pagine (Google Project Management Professional Certificate) e un repo GitHub (BigBoss133/SMOT-PMANAGER) con un'app Python CLI. Vuole creare un tool che:
1. Apre un editor di testo con un template di progetto
2. L'utente scrive il progetto, salva
3. L'AI (basata sulla dispensa) analizza e fornisce feedback
4. Loop iterativo fino a progetto completo
5. Output: Project Plan completo in markdown

### Interview Summary
**Key Discussions**:
- **Interfaccia**: CLI con editor esterno ($EDITOR)
- **Flusso**: Editor → salva → AI analizza (RAG) → feedback → loop (max 10 iterazioni, `--done` per terminare)
- **Output**: 5 deliverables (Project Charter, Stakeholder+RACI, WBS+Schedule, Rischi, Budget)
- **AI**: Ollama locale + API cloud (OpenAI/Claude)
- **Testing**: TDD
- **Scoping**: Estendere repo esistente

### Metis Review
**Identified Gaps** (addressed):
- **Loop termination**: Max 10 iterazioni + flag `--done` → applicato
- **Vector DB**: ChromaDB → applicato
- **PDF extractability**: pdftotext confermato funzionante → applicato
- **CLI command surface**: 5 comandi definiti → applicato
- **Error handling matrix**: fail/warn/continue per ogni scenario → applicato

---

## Work Objectives

### Core Objective
Trasformare SMOT-PMANAGER in uno strumento CLI interattivo che guida l'utente nella creazione di un Project Plan professionale, usando AI (RAG + prompt engineering sulla dispensa) per validare, suggerire e completare il contenuto.

### Concrete Deliverables
- `src/pman/rag.py` — Pipeline RAG con metadata filtering (capitolo/topic)
- `src/pman/editor.py` — Gestione editor esterno e file temporanei
- `src/pman/orchestrator.py` — Loop AI section-based, advisory mode, force-complete
- `src/pman/templates/` — Template markdown con blocchi YAML strutturati
- `src/pman/ai_providers.py` — Provider AI unificato (Ollama + Cloud)
- `src/pman/validator.py` — Validatore YAML deterministico + analisi strutturale
- `src/pman/feedback.py` — Generatore feedback con separazione blocker/warning
- `src/pman/repository.py` — CRUD con modelli espansi (WBSTask, Issue, Risk)
- `src/pman/commands/plan.py` — Comandi CLI (`new/check/continue/status/export/list`)
- `tests/` — Test TDD per ogni modulo

### Definition of Done
- [ ] `pman plan new` apre $EDITOR con template Markdown+YAML, AI analizza se richiesto
- [ ] `pman plan check --section wbs` analisi < 5 secondi (section-based)
- [ ] `pman plan status --force-complete` override utente funzionante
- [ ] `pman plan continue <id>` riprende una sessione esistente
- [ ] `pman plan export --populate-db` popola tabelle WBSTask/Issue/Risk
- [ ] `pman plan list` elenca tutti i progetti
- [ ] Validatore YAML rileva 2 Accountable nella stessa riga RACI
- [ ] RAG metadata filter: query su WBS restituisce SOLO chunk Capitoli 13-14
- [ ] `pytest` → tutti i test passano (copertura ≥ 80%)
- [ ] AI funziona con Ollama locale E con API cloud (OpenAI)

### Must Have
- Pipeline RAG funzionante sulla dispensa completa (134pp)
- Template markdown con tutte le 5 sezioni del Project Plan
- Loop feedback AI con massimo 10 iterazioni
- Persistenza progetti su SQLite
- Graceful degradation: se RAG non disponibile, feedback generico (senza contesto dispensa)

### Must NOT Have (Guardrails)
- ❌ Generazione automatica issue GitHub dal piano
- ❌ Export in PDF/HTML/DOCX — solo Markdown
- ❌ TUI interattiva (curses/textual) — solo batch CLI + editor esterno
- ❌ Calcolo automatico del budget — solo input manuale
- ❌ Grafici Gantt o diagrammi — solo descrizioni testuali
- ❌ Multi-tenant / multi-user
- ❌ Template multipli — un solo template iniziale

---

## Architecture Decisions (5 Falle Risolte)

### 1. Markdown + YAML: Dati Strutturati nei Blocchi

**Problema**: WBS, RACI e Budget in tabelle Markdown sono impossibili da validare deterministicamente. L'AI non può verificare che non ci siano due "Accountable" nella stessa riga RACI.

**Soluzione**: Template con blocchi YAML incastonati nel Markdown:

```markdown
## Stakeholder Analysis + RACI

Descrizione libera degli stakeholder...

```yaml
# BEGIN RACI
raci_matrix:
  - task: "Definire requisiti"
    responsible: "Product Owner"
    accountable: "Project Manager"  # UNICO Accountable
    consulted: ["Tech Lead"]
    informed: ["Stakeholder Board"]
# END RACI
```

Il **Validator** (T8) userà `yaml.safe_load()` per estrarre e validare deterministicamente:
- RACI: esattamente 1 Accountable per task
- Budget: somma costi = totale
- WBS: struttura ad albero senza cicli

L'AI fornirà solo **analisi qualitativa** (es. "I rischi sono pertinenti?"), non validazione strutturale.

### 2. Analisi Section-Based (non Full-Document)

**Problema**: Rianalizzare l'intero documento (2000+ parole) a ogni salvataggio satura la context window e blocca l'utente per decine di secondi.

**Soluzione**: Comando `pman plan check --section <nome>` per feedback mirato:
- Estrae solo la sezione specifica dal Markdown
- Query RAG solo sui capitoli pertinenti (metadata filtering)
- Prompt AI ridotto (solo la sezione + contesto RAG)
- Tempi di risposta < 5 secondi anche su modelli locali

### 3. Paradigma "Advisory, not Mandatory"

**Problema**: LLM locali possono allucinare o essere eccessivamente pedanti, bloccando l'utente.

**Soluzione**:
- `pman plan status --force-complete` — override utente esplicito
- Feedback separato in **Blocker** (errori strutturali: manca Project Charter) e **Warning** (suggerimenti: "Considera di aggiungere più stakeholder")
- L'utente può sempre esportare anche se il validatore non è al 100%

### 4. RAG con Metadata Filtering

**Problema**: Chunking a 512 token + cosine similarity può recuperare frammenti da capitoli sbagliati (es. consigli Agile in un progetto Waterfall).

**Soluzione**: Ogni chunk in ChromaDB ha metadati `{"chapter": "13", "topic": "WBS"}`.
Il retriever (T9) applica **hard filter** sui metadati: per la sezione WBS, cerca solo nei Capitoli 13-14.
Questo elimina il rumore cross-metodologia.

### 5. Database Ready per Execution/Monitoring

**Problema**: Il file Markdown è statico. La dispensa descrive anche Execution e Monitoring (Work Performance Data, Change Request). L'architettura attuale non le supporta.

**Soluzione**: Espandere i modelli SQLAlchemy (T12) con tabelle relazionali:
- `Task` (WBS task tracciati)
- `Issue` (Issue Log)
- `Risk` (Risk Register con probabilità/impatto/stato)

All'export (T18), un hook fa il parsing del Markdown e popola automaticamente queste tabelle.
Questo prepara il terreno per futuri comandi `pman track` e `pman update` senza riscrivere l'architettura.

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: NO (solo `tests/__init__.py` vuoto)
- **Automated tests**: TDD
- **Framework**: pytest + pytest-asyncio (già in dipendenze)
- **Setup incluso**: Sì, come Task T1

### QA Policy
Ogni task include Agent-Executed QA Scenarios.
Evidence salvata in `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — fondazione + scaffolding):
├── T1: Test infrastructure setup [quick]
├── T2: PDF text extraction (PyMuPDF primario, cross-OS) [quick]
├── T3: PDF chunking + embedding pipeline [deep]
├── T4: ChromaDB vector store integration [deep]
├── T5: Config expansion (RAG + AI provider settings) [quick]
├── T6: Project template markdown + YAML generator [quick]
├── T7: Editor invocation (cross-OS: $EDITOR → notepad su Windows) + temp files [quick]
└── T26: CI/CD GitHub Actions workflow [quick]

Wave 2 (After Wave 1 — core logic, MAX PARALLEL):
├── T8: Markdown parser + YAML validator [quick]
├── T9: RAG query pipeline (metadata filtering) [deep]
├── T10: AI feedback generator (blocker/warning separation) [deep]
├── T11: Feedback loop orchestrator (section-based, advisory) [deep]
├── T12: Project CRUD (modelli espansi: WBSTask, Issue, Risk) [quick]
├── T13: Cloud AI provider + Ollama circuit breaker [unspecified-high]
└── T14: Error handling + graceful degradation [quick]

Wave 3 (After Wave 2 — CLI commands):
├── T15: `pman plan new` command [visual-engineering]
├── T16: `pman plan continue` command [quick]
├── T17: `pman plan status --force-complete` command [quick]
├── T18: `pman plan export --populate-db` command [quick]
├── T19: `pman plan list` command [quick]
├── T20: CLI integration + refactoring [quick]
└── T25: `pman backup` command [quick]

Wave 4 (After Wave 3 — integration + polish):
├── T21: End-to-end integration tests [deep]
├── T22: Session recovery (temp file preservation) [quick]
├── T23: Performance optimization (caching, lazy loading) [deep]
└── T24: Refactoring: remove old code, align imports [quick]

Wave FINAL (After ALL tasks — 4 parallel reviews, then user okay):
├── F1: Plan Compliance Audit (oracle)
├── F2: Code Quality Review (unspecified-high)
├── F3: Real Manual QA (unspecified-high + playwright)
├── F4: Scope Fidelity Check (deep)
→ Present results → Get explicit user okay
```

Critical Path: T1 → T6 → T11 → T15 → T21 → T25 → F1-F4 → user okay
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 8 (Waves 1, 2)

### Dependency Matrix

| Task | Blocks | Blocked By |
|------|--------|------------|
| T1 | 8, 9, 11, 12, 21 | — |
| T2 | 3, 4, 9 | — |
| T3 | 4, 9 | 2 (metadata da chapters) |
| T4 | 9 | 3 (metadata negli embeddings) |
| T5 | 10, 13 | — |
| T6 | 7, 8, 11, 15 | — |
| T7 | 11, 15, 22 | 6 (template path) |
| T8 | 11, 17 | 1 (test), 6 (template schema YAML) |
| T9 | 10, 11 | 4 (ChromaDB+metadata), 3 (embeddings) |
| T10 | 11 | 5 (config), 9 (RAG context) |
| T11 | 15, 16 | 8 (validator YAML), 9 (RAG filtered), 10 (feedback), 14 (errors) |
| T12 | 15, 16, 17, 18, 19 | 1 (test) — models.py esteso con WBSTask, Issue, Risk |
| T13 | 15 | 5 (config) — include Ollama circuit breaker |
| T14 | 11, 16 | — |
| T15 | 21 | 6 (template), 7 (editor), 11 (loop), 12 (CRUD), 13 (cloud AI) |
| T16 | 21 | 11 (loop), 12 (CRUD), 14 (errors) |
| T17 | 21 | 8 (validator), 12 (CRUD) |
| T18 | 21 | 12 (CRUD) — export con --populate-db |
| T19 | 21 | 12 (CRUD) |
| T20 | 15-19 | 15-19 |
| T21 | F1-F4 | 15-19 (all CLI), 1 (test) |
| T22 | — | 7 (editor), 14 (errors) |
| T23 | — | 21 (E2E) |
| T24 | — | 21 (E2E) |
| T25 | — | 12 (CRUD) — backup workspace completo |
| T26 | — | — (indipendente) — CI/CD GitHub Actions |

### Agent Dispatch Summary

- **Wave 1**: 8 — T1→quick, T2→quick, T3→deep, T4→deep, T5→quick, T6→quick, T7→quick, T26→quick
- **Wave 2**: 7 — T8→quick, T9→deep, T10→deep, T11→deep, T12→quick, T13→unspecified-high, T14→quick
- **Wave 3**: 7 — T15→visual-engineering, T16-T19→quick, T20→quick, T25→quick
- **Wave 4**: 4 — T21→deep, T22→quick, T23→deep, T24→quick
- **FINAL**: 4 — F1→oracle, F2→unspecified-high, F3→unspecified-high, F4→deep

---

## TODOs

- [ ] 1. **Test Infrastructure Setup**

  **What to do**:
  - Creare `conftest.py` con fixtures: DB in-memory SQLite, client FastAPI test, mock Ollama
  - Creare `tests/test_config.py` — test che tutte le variabili d'ambiente siano caricate
  - Creare `tests/test_models.py` — test creazione Project, Task, validazione enum
  - Configurare pytest in `pyproject.toml` con `asyncio_mode = "auto"` e coverage
  - Aggiungere `pytest-cov` alle dipendenze
  - Verificare con `pytest tests/ -v --cov=src/pman`

  **Must NOT do**:
  - Non testare API (gli endpoint attuali sono stub)
  - Non creare test per moduli che non esistono ancora

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Task standard di configurazione test, pattern ben conosciuti
  - **Skills**: [`testing`]
    - `testing`: Pattern pytest, fixtures, coverage setup

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with T2, T3, T4, T5, T6, T7)
  - **Blocks**: T8, T9, T11, T12, T21
  - **Blocked By**: None

  **References**:
  - `pyproject.toml` — Dipendenze esistenti (pytest, pytest-asyncio già presenti)
  - `src/pman/config.py` — Settings da testare
  - `src/pman/models.py:1-50` — Modelli ORM da testare (Project, Task, enums)

  **Acceptance Criteria**:
  - [ ] `pytest tests/ -v` → almeno 8 test passano
  - [ ] Coverage ≥ 80% su config.py e models.py

  **QA Scenarios**:
  ```
  Scenario: Test infrastructure works
    Tool: Bash
    Preconditions: pyproject.toml has [tool.pytest] config, conftest.py exists
    Steps:
      1. Run: pytest tests/ -v --tb=short
      2. Assert: exit code 0, at least 8 tests collected
      3. Assert: "passed" count ≥ 8
    Expected Result: All tests pass with verbose output
    Failure Indicators: exit code ≠ 0, tests not collected
    Evidence: .sisyphus/evidence/task-1-tests-pass.txt

  Scenario: Coverage report generated
    Tool: Bash
    Steps:
      1. Run: pytest tests/ --cov=src/pman --cov-report=term
      2. Assert: "config.py" coverage ≥ 80%
      3. Assert: "models.py" coverage ≥ 80%
    Expected Result: Coverage report shows high coverage on existing modules
    Evidence: .sisyphus/evidence/task-1-coverage.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `test(pman): add test infrastructure with config and model tests`
  - Files: `conftest.py`, `tests/test_config.py`, `tests/test_models.py`, `pyproject.toml`
  - Pre-commit: `pytest tests/ -q`

- [ ] 2. **PDF Text Extraction Pipeline**

  **What to do**:
  - Creare `src/pman/pdf_extractor.py` con classe `PDFExtractor`
  - Usare `pdftotext` via subprocess (già disponibile nel sistema) o PyMuPDF (fitz)
  - Implementare `extract_text(pdf_path) -> str` che restituisce tutto il testo
  - Implementare `extract_chapters(pdf_path) -> list[Chapter]` che suddivide per capitolo (basato su "CAPITOLO X:" pattern)
  - **CRITICO (Falla 4)**: Ogni `Chapter` DEVE includere `number`, `title`, `topic` (topic mappato dal titolo: es. "WBS" → "wbs", "Rischi" → "risks") come metadati per il RAG metadata filtering
  - Mappatura chapter→topic predefinita: Cap 7 → "charter", Cap 8-9 → "stakeholder/raci", Cap 13-14 → "wbs", Cap 17 → "budget", Cap 18 → "risks", Cap 28-34 → "agile"
  - **CRITICO (OS Portability)**: PyMuPDF (`fitz`) è il motore PRIMARIO. `pdftotext` è fallback opzionale.
    - PyMuPDF è una libreria Python pura: funziona su Linux, macOS e Windows con `pip install pymupdf`
    - `pdftotext` richiede Poppler (non nativo su Windows) → usato solo come fallback se PyMuPDF non disponibile
  - Aggiungere `pymupdf` a pyproject.toml come dipendenza OBBLIGATORIA (non opzionale)
  - Gestire errori: file non trovato, PDF corrotto, testo non estraibile (con messaggio chiaro se nessun motore disponibile)
  - Test TDD: PDF valido, PDF vuoto, PDF inesistente + verifica metadati chapter

  **Must NOT do**:
  - Non fare OCR (se il PDF non è estraibile, errore chiaro)
  - Non estrarre immagini o tabelle

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Task mirato con tool esterno (pdftotext), logica semplice
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: Non serve, test TDD già nel task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T3, T4, T9
  - **Blocked By**: None

  **References**:
  - `/home/michele-finocchiaro/Scrivania/SmotPmanager/Google_PM_Dispensa_Universitaria_LIBRO.pdf` — PDF sorgente
  - `src/pman/config.py` — Pattern Pydantic BaseSettings per la config del path PDF

  **Acceptance Criteria**:
  - [ ] `extract_text(pdf_path)` restituisce > 100K caratteri per la dispensa
  - [ ] `extract_chapters(pdf_path)` restituisce ≥ 35 capitoli
  - [ ] Test coprono: file valido, file inesistente, PDF non estraibile

  **QA Scenarios**:
  ```
  Scenario: PDF extraction produces text
    Tool: Bash (python -c)
    Preconditions: PDF exists at Scrivania/SmotPmanager/
    Steps:
      1. Run: python -c "from pman.pdf_extractor import PDFExtractor; t = PDFExtractor().extract_text('/home/michele-finocchiaro/Scrivania/SmotPmanager/Google_PM_Dispensa_Universitaria_LIBRO.pdf'); print(len(t))"
      2. Assert: output > 100000
      3. Assert: text contains "Project Management"
    Expected Result: Text length > 100K chars
    Failure Indicators: Error on extraction, text length < 100K
    Evidence: .sisyphus/evidence/task-2-extraction.txt

  Scenario: Chapter extraction works
    Tool: Bash (python -c)
    Steps:
      1. Run: python -c "from pman.pdf_extractor import PDFExtractor; chapters = PDFExtractor().extract_chapters('/home/michele-finocchiaro/Scrivania/SmotPmanager/Google_PM_Dispensa_Universitaria_LIBRO.pdf'); print(len(chapters))"
      2. Assert: chapter count ≥ 35
      3. Assert: first chapter title contains "INTRODUZIONE"
    Expected Result: 35+ chapters extracted
    Failure Indicators: chapter count < 35, empty titles
    Evidence: .sisyphus/evidence/task-2-chapters.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(pman): add PDF text extraction pipeline for textbook`
  - Files: `src/pman/pdf_extractor.py`, `tests/test_pdf_extractor.py`

- [ ] 3. **PDF Chunking + Embedding Pipeline**

  **What to do**:
  - Creare `src/pman/embedder.py` con classe `TextEmbedder`
  - Implementare chunking strategy: massimo 512 token per chunk, overlap 50 token, split per paragrafo
  - Supportare embedding via Ollama (`nomic-embed-text` model) E OpenAI (`text-embedding-3-small`)
  - Implementare metodo `embed_chunks(chunks: list[str]) -> list[list[float]]`
  - **CRITICO (Falla 4)**: `chunk_text()` DEVE restituire `list[Chunk]` dove ogni Chunk ha `text`, `chapter_number`, `topic` — i metadati del capitolo vengono propagati dal PDFExtractor
  - Batch processing per ottimizzare chiamate API
  - Processare l'intera dispensa: ~134 pagine → ~200-300 chunk
  - Test TDD: chunk size, overlap, embedding dimensions (768 per nomic, 1536 per OpenAI) + metadati preservati

  **Must NOT do**:
  - Non hardcodare il modello di embedding
  - Non processare l'intera dispensa a ogni avvio (usare cache)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Richiede comprensione di NLP/chunking strategies e gestione batch processing
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: Pattern TDD già nel task

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T4, T9
  - **Blocked By**: T2

  **References**:
  - `src/pman/ollama.py` — Pattern client Ollama esistente (da rendere async)
  - `src/pman/config.py` — Settings Ollama (host, model)
  - Context7: "langchain text splitter recursive character" — Pattern chunking

  **Acceptance Criteria**:
  - [ ] Chunk size massimo 512 token con overlap 50
  - [ ] Embedding dimension corretto per il modello selezionato
  - [ ] Test: chunk vuoto → errore, lista vuota → lista vuota

  **QA Scenarios**:
  ```
  Scenario: Chunking produces correct sizes
    Tool: Bash (python -c)
    Steps:
      1. Run chunking su testo di test di 2000 token
      2. Assert: number of chunks = ceil(2000/(512-50)) ≈ 5
      3. Assert: every chunk ≤ 512 tokens
    Expected Result: Correct number and size of chunks
    Evidence: .sisyphus/evidence/task-3-chunks.txt

  Scenario: Embedding produces correct dimensions
    Tool: Bash (python -c)
    Preconditions: Ollama running with nomic-embed-text
    Steps:
      1. Run embedding on 3 test chunks
      2. Assert: output is list of 3 vectors
      3. Assert: each vector has 768 dimensions (nomic-embed-text)
    Expected Result: Correct embedding dimensions
    Evidence: .sisyphus/evidence/task-3-embeddings.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(pman): add text chunking and embedding pipeline`
  - Files: `src/pman/embedder.py`, `tests/test_embedder.py`

- [ ] 4. **ChromaDB Vector Store Integration**

  **What to do**:
  - Creare `src/pman/vector_store.py` con classe `VectorStore`
  - Integrare ChromaDB (pip install chromadb)
  - Implementare `add_documents(chunks, embeddings, metadata)` — indicizza chunk con metadati (chapter_number, topic, titolo capitolo)
  - **CRITICO (Falla 4)**: `search(query_embedding, k=5, filter_metadata=None)`:
    - Se `filter_metadata={"topic": "wbs"}` → cerca SOLO nei chunk con topic="wbs"
    - Usare `where` clause di ChromaDB per hard filter pre-query
  - Implementare `search_by_section(section_name: str, ...)` che mappa automaticamente section→topic filter
  - Implementare `is_initialized() -> bool` — verifica se il DB ha dati
  - Implementare `initialize_from_pdf(pdf_path)` — pipeline completa: estrai → chunk → embed → store (con metadati)
  - Aggiungere `chromadb` a pyproject.toml
  - Test TDD: store vuoto, search con filter, search senza filter, inizializzazione doppia (idempotente)

  **Must NOT do**:
  - Non usare ChromaDB in modalità client-server (solo embedded/PersistentClient)
  - Non esporre il DB su rete

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integrazione libreria esterna con pattern di caching e idempotenza
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: Pattern coperto da TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T9
  - **Blocked By**: T3

  **References**:
  - `src/pman/config.py` — Aggiungere `chroma_path` e `chroma_collection` settings
  - Context7: "chromadb python PersistentClient add documents" — API ChromaDB

  **Acceptance Criteria**:
  - [ ] `initialize_from_pdf(pdf_path)` completa senza errori (< 60s)
  - [ ] `search(embedding, k=3)` restituisce 3 risultati rilevanti
  - [ ] Seconda `initialize_from_pdf` non duplica dati (idempotente)

  **QA Scenarios**:
  ```
  Scenario: Vector store initialization
    Tool: Bash (python -c)
    Preconditions: PDF extracted, chunks embedded
    Steps:
      1. Run: initialize_from_pdf(pdf_path)
      2. Assert: is_initialized() returns True
      3. Run search with test query embedding
      4. Assert: returns 5 results with relevance scores
    Expected Result: Store initialized, search works
    Evidence: .sisyphus/evidence/task-4-init.txt

  Scenario: Idempotent initialization
    Tool: Bash (python -c)
    Steps:
      1. Run initialize_from_pdf twice
      2. Assert: document count unchanged (no duplicates)
    Expected Result: No duplicate documents
    Evidence: .sisyphus/evidence/task-4-idempotent.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(pman): add ChromaDB vector store with RAG pipeline`
  - Files: `src/pman/vector_store.py`, `tests/test_vector_store.py`

- [ ] 5. **Config Expansion (RAG + AI Provider Settings)**

  **What to do**:
  - Estendere `src/pman/config.py` con nuove sezioni:
    - `RAGSettings`: `pdf_path`, `chunk_size`, `chunk_overlap`, `chroma_path`, `chroma_collection`, `top_k`
    - `AIProviderSettings`: `provider` (ollama/openai), `ollama_model`, `openai_model`, `openai_api_key`, `max_tokens`, `temperature`
    - `ProjectSettings`: `projects_dir` (dove salvare i file .md)
  - Aggiungere property helper: `embedding_model` (auto-select in base al provider)
  - Assicurare retrocompatibilità con settings esistenti (GitHub, Ollama, DB)
  - Test TDD: validazione valori predefiniti, override da env, path non esistenti

  **Must NOT do**:
  - Non rimuovere settings esistenti
  - Non esporre API key nei log

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Estensione di file esistente con pattern Pydantic già noto
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: Pattern coperto da TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T10, T13
  - **Blocked By**: None

  **References**:
  - `src/pman/config.py` — File esistente da estendere
  - `.env.example` — Variabili d'ambiente di esempio da aggiornare

  **Acceptance Criteria**:
  - [ ] Tutti i nuovi settings hanno valori predefiniti validi
  - [ ] `embedding_model` property restituisce modello corretto per provider
  - [ ] Test coprono: default, env override, validation error

  **QA Scenarios**:
  ```
  Scenario: Config loads with defaults
    Tool: Bash (python -c)
    Steps:
      1. Run: from pman.config import settings; print(settings.rag_chunk_size)
      2. Assert: output is 512 (default)
    Expected Result: Default values loaded
    Evidence: .sisyphus/evidence/task-5-defaults.txt

  Scenario: Env override works
    Tool: Bash
    Steps:
      1. Run: RAG_CHUNK_SIZE=256 python -c "from pman.config import settings; print(settings.rag_chunk_size)"
      2. Assert: output is 256
    Expected Result: Env var overrides default
    Evidence: .sisyphus/evidence/task-5-env-override.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(pman): add RAG and AI provider configuration settings`
  - Files: `src/pman/config.py`, `.env.example`

- [ ] 6. **Project Template Markdown Generator**

  **What to do**:
  - Creare `src/pman/templates/project_plan.md` — template con **blocchi YAML** incastonati nel Markdown:
    1. **Project Charter**: testo libero (obiettivi, scope, vincoli, assunzioni)
    2. **Stakeholder Analysis + RACI**: descrizione libera + blocco `# BEGIN RACI` / `# END RACI` con matrice YAML strutturata
    3. **Work Breakdown Structure + Schedule**: descrizione + blocco `# BEGIN WBS` / `# END WBS` YAML
    4. **Risk Analysis**: testo libero (analisi qualitativa) + blocco `# BEGIN RISKS` / `# END RISKS` YAML
    5. **Budget + Cost Estimation**: descrizione + blocco `# BEGIN BUDGET` / `# END BUDGET` YAML
  - **CRITICO (Falla 1)**: I blocchi YAML sono validabili deterministicamente. Esempio RACI:
    ```yaml
    # BEGIN RACI
    raci_matrix:
      - task: "Definire requisiti"
        responsible: "Product Owner"
        accountable: "Project Manager"  # ESATTAMENTE 1
        consulted: ["Tech Lead"]
        informed: ["Stakeholder Board"]
    # END RACI
    ```
  - Implementare `TemplateGenerator` in `src/pman/templates.py`:
    - `generate() -> str` — restituisce il template con placeholder e blocchi YAML vuoti
    - `get_sections() -> list[str]` — lista nomi sezioni obbligatorie
    - `get_yaml_blocks() -> list[str]` — lista nomi blocchi YAML attesi ("RACI", "WBS", "RISKS", "BUDGET")
  - Aggiungere commenti guida nel template (`<!-- Inserisci qui gli obiettivi SMART -->`)
  - Test TDD: template contiene tutte le 5 sezioni + 4 blocchi YAML, placeholder sono sostituibili

  **Must NOT do**:
  - Non creare più di 1 template
  - Non includere contenuti precompilati — solo struttura e placeholder

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Generazione template markdown, logica semplice
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: Coperto da TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T7, T8, T11, T15
  - **Blocked By**: None

  **References**:
  - `/home/michele-finocchiaro/Scrivania/SmotPmanager/Google_PM_Dispensa_Universitaria_LIBRO.pdf` (Capitoli 7, 8, 9, 13, 17, 18) — Struttura Project Charter, RACI, WBS, Budget, Rischi

  **Acceptance Criteria**:
  - [ ] Template contiene 5 sezioni con commenti guida
  - [ ] `get_sections()` restituisce lista di 5 nomi sezione
  - [ ] Test: template valid markdown, tutte le sezioni presenti

  **QA Scenarios**:
  ```
  Scenario: Template has all required sections
    Tool: Bash (python -c)
    Steps:
      1. Run: from pman.templates import TemplateGenerator; t = TemplateGenerator().generate(); print(t)
      2. Assert: contains "Project Charter"
      3. Assert: contains "Stakeholder" and "RACI"
      4. Assert: contains "Work Breakdown Structure"
      5. Assert: contains "Risk Analysis"
      6. Assert: contains "Budget"
    Expected Result: All 5 sections present with placeholder markers
    Evidence: .sisyphus/evidence/task-6-template.txt

  Scenario: Template is valid markdown
    Tool: Bash
    Steps:
      1. Write template to /tmp/test-template.md
      2. Verify it's valid markdown (headings, lists, tables)
    Expected Result: Parseable markdown
    Evidence: .sisyphus/evidence/task-6-markdown.md
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(pman): add project plan markdown template with 5 sections`
  - Files: `src/pman/templates/project_plan.md`, `src/pman/templates.py`, `tests/test_templates.py`

- [ ] 7. **Editor Invocation + Temp File Management**

  **What to do**:
  - Creare `src/pman/editor.py` con classe `EditorManager`
  - Implementare `open_editor(template: str, project_name: str) -> str`:
    - Crea file temporaneo in `~/.pman/projects/{name}/draft.md`
    - Popola con il template
    - **CRITICO (OS Portability)**: Rilevamento OS con `platform.system()`:
      - **Linux/macOS**: `$EDITOR` → `nano` → `vim` (fallback a catena)
      - **Windows**: `$EDITOR` → `notepad` → prova `code --wait` (VS Code)
    - Attende chiusura editor
    - Restituisce contenuto del file
  - Implementare `save_snapshot(content, project_id, iteration)` — salva versione per recovery
  - Implementare `get_latest_content(project_id) -> str | None` — recupera ultima versione
  - Gestire errori: $EDITOR non settato, editor crash, file vuoto, disco pieno
  - Test TDD: editor con `EDITOR=cat` per test deterministici

  **Must NOT do**:
  - Non implementare TUI integrata
  - Non tracciare modifiche in tempo reale (solo al salvataggio)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Gestione file system + subprocess, pattern noti
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: Coperto da TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: T11, T15, T22
  - **Blocked By**: T6 (template path)

  **References**:
  - `src/pman/config.py` — Aggiungere `projects_dir` setting
  - `src/pman/cli.py` — Pattern comandi Typer esistenti

  **Acceptance Criteria**:
  - [ ] `open_editor(template, "test")` con `EDITOR=cat` restituisce il template
  - [ ] File salvato in `~/.pman/projects/{name}/`
  - [ ] `save_snapshot` + `get_latest_content` roundtrip corretto
  - [ ] Test: EDITOR non settato → fallback a nano/vim con warning

  **QA Scenarios**:
  ```
  Scenario: Editor opens and returns content
    Tool: Bash
    Preconditions: Template file exists
    Steps:
      1. Run: EDITOR=cat python -c "from pman.editor import EditorManager; print(EditorManager().open_editor('# Test', 'test-project'))"
      2. Assert: output contains "# Test"
      3. Assert: file created at ~/.pman/projects/test-project/draft.md
    Expected Result: Template content returned, file saved
    Evidence: .sisyphus/evidence/task-7-editor.txt

  Scenario: Empty editor save is handled
    Tool: Bash
    Steps:
      1. Run: EDITOR="cp /dev/null" python -c "from pman.editor import EditorManager; EditorManager().open_editor('# Template', 'empty-test')"
      2. Assert: warning message about empty file
      3. Assert: returns empty string (not original template)
    Expected Result: Empty content handled gracefully
    Evidence: .sisyphus/evidence/task-7-empty-editor.txt
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `feat(pman): add editor invocation and temp file management`
  - Files: `src/pman/editor.py`, `tests/test_editor.py`

- [ ] 8. **Markdown Parser + Section Validator**

  **What to do**:
  - Creare `src/pman/validator.py` con classe `ProjectValidator`
  - Implementare `parse_sections(content: str) -> dict[str, str]` — estrae le 5 sezioni dal markdown
  - **CRITICO (Falla 1)**: `parse_yaml_blocks(content: str) -> dict[str, dict]`:
    - Estrae blocchi tra `# BEGIN X` e `# END X` usando `yaml.safe_load()`
    - Restituisce dict con chiavi: "raci", "wbs", "risks", "budget"
  - **CRITICO (Falla 1)**: Validazione DETERMINISTICA (non AI) dei blocchi YAML:
    - `validate_raci(raci_data) -> list[str]`: verifica ESATTAMENTE 1 Accountable per task, nomi ruoli validi
    - `validate_budget(budget_data) -> list[str]`: verifica somma costi = totale dichiarato
    - `validate_wbs(wbs_data) -> list[str]`: verifica struttura ad albero senza cicli/orfani
  - Implementare `check_completeness(sections) -> CompletenessReport`:
    - Combina validazione YAML (deterministica) + sezioni testo (presenza, word_count)
    - Report separato: `yaml_errors` (bloccanti), `text_warnings` (suggerimenti)
  - Test TDD: YAML valido, YAML con 2 Accountable, budget non bilanciato, WBS con task orfano

  **Must NOT do**:
  - Non validare semantica del testo libero (lasciato all'AI)
  - Non usare regex per parsing YAML — usare `yaml.safe_load()`

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Parsing markdown + regole di validazione, complessità media
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: Coperto da TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T11, T17
  - **Blocked By**: T1 (test fixtures), T6 (template schema)

  **References**:
  - `src/pman/templates/project_plan.md` — Template per conoscere heading esatti delle sezioni
  - Context7: "python markdown parser extract headings sections" — Libreria parsing

  **Acceptance Criteria**:
  - [ ] `parse_sections(template)` restituisce dict con 5 chiavi
  - [ ] `check_completeness(template_vuoto).overall_score == 0`
  - [ ] `check_completeness(template_completo).overall_score == 100`
  - [ ] Test coprono: 0%, 50%, 100% completezza

  **QA Scenarios**:
  ```
  Scenario: Full template scores 100%
    Tool: Bash (python -c)
    Steps:
      1. Load template, fill all sections with >50 words each
      2. Run: check_completeness(parse_sections(content))
      3. Assert: overall_score == 100, missing_sections == []
    Expected Result: 100% completeness
    Evidence: .sisyphus/evidence/task-8-full-score.txt

  Scenario: Empty template scores 0%
    Tool: Bash (python -c)
    Steps:
      1. Run check_completeness on empty template
      2. Assert: overall_score < 20, all 5 sections in missing_sections
    Expected Result: Low completeness score
    Evidence: .sisyphus/evidence/task-8-empty-score.txt

  Scenario: Partial template scores ~60%
    Tool: Bash (python -c)
    Steps:
      1. Fill 3 of 5 sections with content
      2. Assert: overall_score ≈ 60, missing_sections length == 2
    Expected Result: 60% completeness
    Evidence: .sisyphus/evidence/task-8-partial-score.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(pman): add markdown parser and project completeness validator`
  - Files: `src/pman/validator.py`, `tests/test_validator.py`

- [ ] 9. **RAG Query Pipeline (Search + Context Building)**

  **What to do**:
  - Completare `src/pman/rag.py` con classe `RAGPipeline`
  - **CRITICO (Falla 4)**: `query(question: str, k: int = 5, section_filter: str = None) -> RAGContext`:
    - Se `section_filter="wbs"` → mappa a topic="wbs" → hard filter `where={"topic": "wbs"}` su ChromaDB
    - Questo GARANTISCE che per la sezione WBS vengano recuperati solo chunk dei Capitoli 13-14, non frammenti sparsi
  - `query_section(section_name: str) -> RAGContext`: mappa automaticamente section→topic (charter→"charter", raci→"stakeholder/raci", wbs→"wbs", risks→"risks", budget→"budget")
  - Aggiungere caching: stessa query+filter = risultato cached (TTL: 5 minuti)
  - Test TDD: query senza filter, query con filter wbs (solo chunk WBS), filter inesistente → 0 risultati

  **Must NOT do**:
  - Non esporre l'implementazione interna del vector store
  - Non fare embedding senza cache (costo computazionale)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Pipeline RAG con embedding, caching, formatting — complessità alta
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T10, T11
  - **Blocked By**: T4 (ChromaDB), T3 (embeddings)

  **References**:
  - `src/pman/vector_store.py` — API ChromaDB
  - `src/pman/embedder.py` — API embedding
  - `src/pman/config.py` — `rag_top_k` setting

  **Acceptance Criteria**:
  - [ ] `query("Come si scrive un Project Charter?")` restituisce ≥ 3 chunk rilevanti
  - [ ] `query_section("Project Charter")` restituisce contesto specifico
  - [ ] Stessa query due volte = seconda volta da cache (< 1ms)
  - [ ] Test: vector store vuoto → `RAGContext` vuoto + warning

  **QA Scenarios**:
  ```
  Scenario: RAG query returns relevant context
    Tool: Bash (python -c)
    Preconditions: Vector store initialized with textbook
    Steps:
      1. Run: query("Tripla restrizione project management")
      2. Assert: len(result.chunks) ≥ 3
      3. Assert: formatted_context contains "Scope", "Costo", "Tempo"
    Expected Result: Relevant chunks about triple constraint
    Evidence: .sisyphus/evidence/task-9-rag-query.txt

  Scenario: Cache hit is fast
    Tool: Bash (python -c)
    Steps:
      1. First query (cold): measure time
      2. Second query (cached): measure time
      3. Assert: cached time < 1ms
    Expected Result: Cache hit < 1ms
    Evidence: .sisyphus/evidence/task-9-cache.txt

  Scenario: Empty store returns empty context
    Tool: Bash (python -c)
    Preconditions: No vector store initialized
    Steps:
      1. Run query before initialization
      2. Assert: result.chunks == [], warning message shown
    Expected Result: Graceful empty result
    Evidence: .sisyphus/evidence/task-9-empty-store.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(pman): add RAG query pipeline with caching`
  - Files: `src/pman/rag.py`, `tests/test_rag.py`

- [ ] 10. **AI Feedback Generator (Prompt Engineering + LLM)**

  **What to do**:
  - Creare `src/pman/ai_providers.py`:
    - Classe base `AIProvider` con metodo astratto `generate(prompt, system_prompt)`
    - `OllamaProvider` — wrapping async su `ollama.py` esistente
    - `OpenAIProvider` — API OpenAI (usando httpx async)
    - `AIFactory.create(settings) -> AIProvider` — factory pattern
  - Creare `src/pman/feedback.py` con classe `FeedbackGenerator`:
    - `generate_feedback(content, validator_report, rag_context, section: str = None) -> FeedbackResult`
    - **CRITICO (Falla 3)**: `FeedbackResult` ha DUE liste separate:
      - `blockers: list[str]` — errori strutturali (manca Project Charter, RACI ha 2 Accountable, budget non bilanciato)
      - `warnings: list[str]` — suggerimenti qualitativi ("Considera di aggiungere più stakeholder", "Il rischio X potrebbe essere sottostimato")
    - **CRITICO (Falla 2)**: Se `section` è specificato, il prompt include SOLO quella sezione (+ contesto RAG filtrato), non l'intero documento
    - System prompt: "Sei un project manager. Separa ERRORI STRUTTURALI da SUGGERIMENTI. Sii conciso."
    - Usa AIFactory per il provider configurato
  - Test TDD: mock provider per test deterministici, verifica separazione blockers/warnings

  **Must NOT do**:
  - Non hardcodare prompt in italiano nel codice — usare template file
  - Non chiamare AI se il validator report è al 100%

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Factory pattern, provider multipli, prompt engineering — complessità alta
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD con mock

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T11
  - **Blocked By**: T5 (config), T9 (RAG context)

  **References**:
  - `src/pman/ollama.py` — Client Ollama esistente (da rendere async)
  - `src/pman/config.py` — AI provider settings
  - Context7: "openai python async chat completions api" — API OpenAI

  **Acceptance Criteria**:
  - [ ] `AIFactory.create(ollama_config)` restituisce `OllamaProvider`
  - [ ] `AIFactory.create(openai_config)` restituisce `OpenAIProvider`
  - [ ] `generate_feedback` non chiama AI se completeness = 100%
  - [ ] Mock test: feedback contiene riferimenti alle sezioni mancanti

  **QA Scenarios**:
  ```
  Scenario: AIFactory selects correct provider
    Tool: Bash (python -c)
    Steps:
      1. Create config with provider="ollama"
      2. Assert: isinstance(provider, OllamaProvider)
      3. Change config to provider="openai"
      4. Assert: isinstance(provider, OpenAIProvider)
    Expected Result: Correct provider class selected
    Evidence: .sisyphus/evidence/task-10-factory.txt

  Scenario: No AI call when project is complete
    Tool: Bash (python -c)
    Preconditions: Mock validator returns 100%
    Steps:
      1. Generate feedback with 100% completeness
      2. Assert: response contains "completo" and no AI call was made
    Expected Result: Skip AI, return completion message
    Evidence: .sisyphus/evidence/task-10-complete-skip.txt

  Scenario: Feedback addresses missing sections
    Tool: Bash (python -c)
    Preconditions: Mock validator returns ["Risk Analysis", "Budget"] missing
    Steps:
      1. Generate feedback with mock RAG context
      2. Assert: response mentions "Risk Analysis" and "Budget"
      3. Assert: response includes suggestions from textbook context
    Expected Result: Targeted feedback for missing sections
    Evidence: .sisyphus/evidence/task-10-feedback.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(pman): add AI provider factory and feedback generator`
  - Files: `src/pman/ai_providers.py`, `src/pman/feedback.py`, `tests/test_ai_providers.py`, `tests/test_feedback.py`

- [ ] 11. **Feedback Loop Orchestrator**

  **What to do**:
  - Creare `src/pman/orchestrator.py` con classe `FeedbackLoop`
  - **CRITICO (Falla 2)**: Supportare DUE modalità:
    1. `run_full(project_name)` — loop completo su tutto il documento (per `plan new`)
    2. `run_section(project_name, section_name)` — analisi mirata su UNA sezione (per `plan check --section`)
  - **CRITICO (Falla 3)**: Paradigma "Advisory, not Mandatory":
    - Il loop NON blocca mai l'utente: a 100% chiede conferma ma permette export anche a < 100%
    - `force_complete()` — metodo per marcare il progetto come completato indipendentemente dal validatore
    - I blocker YAML sono mostrati in ROSSO, i warning in GIALLO — solo i blocker sono "raccomandati", mai "obbligatori"
  - `run_full` loop (max 10 iterazioni):
    1. Apri editor con contenuto attuale
    2. Se flag `## STATUS: COMPLETO` o `--done` → esci
    3. Parsa sezioni + parsing YAML deterministico
    4. Per ogni sezione: mostra stato (YAML errori + testo warning)
    5. L'utente sceglie: continuare, saltare a sezione specifica, o forzare completamento
    6. Genera feedback AI (se l'utente lo richiede)
    7. Salva snapshot
  - Implementare `display_feedback(feedback: FeedbackResult)` — blockers in rosso, warnings in giallo (Rich)
  - Test TDD: loop termina a 100%, `--done`, `force_complete()`, sezione singola

  **Must NOT do**:
  - Non superare 10 iterazioni
  - MAI bloccare l'export — l'utente può sempre esportare
  - Non forzare l'AI a runnare — l'utente sceglie se chiamarla

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Orchestrazione complessa multi-step con stato e recovery
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: NO (dipende da molti moduli)
  - **Parallel Group**: Wave 2 (sequenziale dopo T8-T10, T14)
  - **Blocks**: T15, T16
  - **Blocked By**: T8 (validator), T9 (RAG), T10 (feedback), T14 (errors)

  **References**:
  - `src/pman/editor.py` — Editor Manager
  - `src/pman/validator.py` — Project Validator
  - `src/pman/rag.py` — RAG Pipeline
  - `src/pman/feedback.py` — Feedback Generator
  - `src/pman/cli.py` — Pattern Rich output (tabelle, pannelli)

  **Acceptance Criteria**:
  - [ ] Loop termina a 100% completezza
  - [ ] Loop termina con flag `--done` nel file
  - [ ] Loop forza terminazione a iterazione 10 con messaggio
  - [ ] Feedback mostrato con Rich formatting (pannelli, colori)
  - [ ] Test: loop con tutte sezioni complete → 1 iterazione

  **QA Scenarios**:
  ```
  Scenario: Loop completes when all sections filled
    Tool: Bash
    Preconditions: Mock editor returns complete template
    Steps:
      1. Run: FeedbackLoop().run("test-complete")
      2. Assert: loop exits after 1 iteration
      3. Assert: output contains "Progetto completo!"
    Expected Result: Single iteration, success message
    Evidence: .sisyphus/evidence/task-11-complete.txt

  Scenario: Loop terminates at max iterations
    Tool: Bash
    Preconditions: Mock editor returns empty every time
    Steps:
      1. Run: FeedbackLoop().run("test-stubborn")
      2. Assert: loop runs exactly 10 iterations
      3. Assert: output contains "Raggiunto limite massimo"
    Expected Result: 10 iterations, warning message
    Evidence: .sisyphus/evidence/task-11-max-iter.txt

  Scenario: --done flag exits loop early
    Tool: Bash
    Preconditions: Mock editor returns content with "## STATUS: COMPLETO"
    Steps:
      1. Run loop with done flag in content
      2. Assert: exits immediately (1 iteration)
    Expected Result: Early exit on done signal
    Evidence: .sisyphus/evidence/task-11-done-flag.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(pman): add feedback loop orchestrator`
  - Files: `src/pman/orchestrator.py`, `tests/test_orchestrator.py`

- [ ] 12. **Project CRUD Operations (SQLite Persistence)**

  **What to do**:
  - Creare `src/pman/database.py`:
    - `init_db()` — crea tabelle (Base.metadata.create_all)
    - `get_session()` — async session factory con SQLAlchemy async
  - **CRITICO (Falla 5)**: Espandere `src/pman/models.py` con tabelle per la fase di Execution:
    - `WBSTask`: id, project_id FK, parent_id FK (self-referential), title, description, status, assigned_to, estimated_hours, actual_hours, start_date, due_date
    - `Issue`: id, project_id FK, title, description, severity, status, reported_by, assigned_to, resolution
    - `Risk`: id, project_id FK, title, description, probability (1-5), impact (1-5), score (P×I), category, mitigation, contingency, status, owner
    - Aggiornare `Project`: aggiungere campo `phase` (PLANNING/EXECUTION/MONITORING/CLOSED)
  - Creare `src/pman/repository.py` con classe `ProjectRepository`:
    - `create/get_by_id/get_by_name/list_all/update_status/save_snapshot` (base)
    - `create_wbs_task/create_issue/create_risk` (execution)
    - `get_wbs_tree(project_id)` — albero WBS ricorsivo
    - `get_risk_matrix(project_id)` — matrice probabilità×impatto
  - Aggiungere `aiosqlite` a dipendenze
  - Test TDD: CRUD completo, constraint unique name, WBS tree traversal, risk score calculation

  **Must NOT do**:
  - Non usare sessioni sincrone
  - Non fare migrazioni Alembic in questo task (solo create_all per ora)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: CRUD pattern standard con SQLAlchemy async
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T15, T16, T17, T18, T19
  - **Blocked By**: T1 (test fixtures)

  **References**:
  - `src/pman/models.py` — Modelli ORM esistenti
  - `src/pman/config.py` — `sqlalchemy_database_uri` property
  - Context7: "sqlalchemy 2.0 async session create_all" — Pattern async

  **Acceptance Criteria**:
  - [ ] `create + get_by_id` roundtrip corretto
  - [ ] `get_by_name("duplicate")` dopo `create` solleva IntegrityError
  - [ ] `list_all()` restituisce tutti i progetti
  - [ ] `save_snapshot` aggiorna metadata JSON

  **QA Scenarios**:
  ```
  Scenario: Full CRUD lifecycle
    Tool: Bash (python -c)
    Preconditions: init_db() called
    Steps:
      1. Create project "TestP1"
      2. Get by id → assert name == "TestP1"
      3. Update status to IN_PROGRESS
      4. Get by id → assert status == IN_PROGRESS
      5. List all → assert len == 1
    Expected Result: All CRUD operations work
    Evidence: .sisyphus/evidence/task-12-crud.txt

  Scenario: Unique name constraint
    Tool: Bash (python -c)
    Steps:
      1. Create project "UniqueTest"
      2. Try create project "UniqueTest" again
      3. Assert: IntegrityError raised
    Expected Result: Duplicate name rejected
    Evidence: .sisyphus/evidence/task-12-unique.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(pman): add project CRUD with async SQLAlchemy persistence`
  - Files: `src/pman/database.py`, `src/pman/repository.py`, `tests/test_repository.py`

- [ ] 13. **AI Provider Integration (Cloud + Ollama Circuit Breaker)**

  **What to do**:
  - Implementare `OpenAIProvider` in `src/pman/ai_providers.py`:
    - Usare `httpx.AsyncClient` per API OpenAI (`/v1/chat/completions`)
    - Supportare `gpt-4o-mini` e `gpt-4o` modelli
    - Gestire rate limiting (retry con exponential backoff)
  - Aggiungere `ClaudeProvider` opzionale (API Anthropic)
  - **CRITICO (Circuit Breaker)**: Aggiungere circuit breaker anche a `OllamaProvider`:
    - Timeout esplicito di 15 secondi per il primo token (TTFT — Time To First Token)
    - Timeout totale di 120 secondi per la generazione completa
    - Se Ollama non risponde entro 15s → interrompere la richiesta, mostrare messaggio "Ollama non risponde. Provare con --provider openai o riprovare più tardi."
    - Circuit breaker stateful: 3 timeout consecutivi → disabilita Ollama per la sessione corrente
  - Aggiungere timeout configurabili in `config.py`: `ollama_timeout_first_token`, `ollama_timeout_total`
  - Test TDD: mock httpx per test deterministici, test rate limit retry, test circuit breaker

  **Must NOT do**:
  - Non hardcodare API key
  - Non chiamare cloud se provider è "ollama"
  - Non bloccare il terminale per più di 15s senza feedback

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Integrazione API + pattern circuit breaker, complessità medio-alta
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD con mock

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T15
  - **Blocked By**: T5 (config)

  **References**:
  - `src/pman/ai_providers.py` — Base class creata in T10
  - `src/pman/config.py` — OpenAI settings
  - `src/pman/github.py` — Pattern httpx.AsyncClient (da replicare)
  - Context7: "openai python httpx async chat completions" — API reference

  **Acceptance Criteria**:
  - [ ] `OpenAIProvider.generate("Hello")` restituisce risposta testuale
  - [ ] Rate limit → retry con backoff (max 3 tentativi)
  - [ ] Timeout 30s → eccezione chiara
  - [ ] Test mock: verifica header Authorization, body format

  **QA Scenarios**:
  ```
  Scenario: OpenAI provider sends correct request
    Tool: Bash (pytest with mock)
    Steps:
      1. Mock httpx to return {"choices":[{"message":{"content":"test"}}]}
      2. Call generate("Hello")
      3. Assert: request body has model="gpt-4o-mini", messages=[...]
    Expected Result: Correct API call format
    Evidence: .sisyphus/evidence/task-13-openai-request.txt

  Scenario: Rate limit triggers retry
    Tool: Bash (pytest with mock)
    Steps:
      1. Mock httpx: first 2 calls = 429, 3rd call = 200
      2. Call generate with retry config
      3. Assert: 3 attempts made, final response = 200
    Expected Result: Retry after rate limit
    Evidence: .sisyphus/evidence/task-13-retry.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(pman): add OpenAI and Claude cloud AI providers`
  - Files: `src/pman/ai_providers.py`, `tests/test_ai_providers.py`

- [ ] 14. **Error Handling + Graceful Degradation**

  **What to do**:
  - Creare `src/pman/errors.py`:
    - Classi eccezione custom: `PMANError`, `EditorError`, `AIError`, `RAGError`, `ConfigError`
    - `handle_error(error, context) -> str` — formatta messaggio utente
  - Implementare graceful degradation in `orchestrator.py`:
    - Ollama non disponibile → fallback a cloud (se configurato)
    - Cloud non disponibile → fallback a feedback generico (senza RAG)
    - RAG store vuoto → feedback senza contesto dispensa (solo validazione struttura)
    - PDF non trovato → RAG disabilitato, warning all'utente
    - Editor crash → recupero da ultimo snapshot
  - Implementare `ErrorRecovery` in `editor.py`:
    - `recover_latest_snapshot(project_id) -> str | None`
  - Test TDD: ogni scenario di errore ha un test

  **Must NOT do**:
  - Non mostrare stack trace all'utente (solo messaggio chiaro)
  - Non interrompere il loop per errori recuperabili

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pattern error handling + recovery, ben definito
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2
  - **Blocks**: T11, T16, T22
  - **Blocked By**: None

  **References**:
  - `src/pman/orchestrator.py` — Punto di integrazione error handling
  - `src/pman/editor.py` — Recovery snapshots

  **Acceptance Criteria**:
  - [ ] Ollama down → tenta cloud → se cloud down → feedback generico
  - [ ] PDF mancante → warning + RAG disabilitato
  - [ ] Editor crash → recupera ultimo snapshot
  - [ ] Ogni eccezione custom ha messaggio utente chiaro (no stack trace)

  **QA Scenarios**:
  ```
  Scenario: Full degradation chain (Ollama → Cloud → Generic)
    Tool: Bash (python -c)
    Preconditions: Ollama down, no OpenAI key
    Steps:
      1. Run feedback loop with all AI providers unavailable
      2. Assert: warning about missing AI providers
      3. Assert: feedback still generated (structure-only, no RAG)
    Expected Result: Graceful degradation, no crash
    Evidence: .sisyphus/evidence/task-14-degradation.txt

  Scenario: Editor crash recovery
    Tool: Bash
    Preconditions: Previous snapshot saved
    Steps:
      1. Simulate editor crash (kill process)
      2. Call recover_latest_snapshot(project_id)
      3. Assert: last content returned, not empty
    Expected Result: Recovery from snapshot
    Evidence: .sisyphus/evidence/task-14-recovery.txt

  Scenario: Missing PDF handled
    Tool: Bash (python -c)
    Steps:
      1. Set PDF path to nonexistent file
      2. Start loop
      3. Assert: warning "Dispensa non trovata, RAG disabilitato"
      4. Assert: loop continues without RAG
    Expected Result: Warning, continue without RAG
    Evidence: .sisyphus/evidence/task-14-missing-pdf.txt
  ```

  **Commit**: YES (groups with Wave 2)
  - Message: `feat(pman): add error handling and graceful degradation`
  - Files: `src/pman/errors.py`, `src/pman/orchestrator.py`, `src/pman/editor.py`, `tests/test_errors.py`

- [ ] 15. **`pman plan new` Command**

  **What to do**:
  - Aggiungere comando `plan` con sottocomandi a `src/pman/cli.py`:
    ```
    pman plan new [--name NAME] [--editor EDITOR] [--provider {ollama,openai}]
    pman plan check --section {charter|raci|wbs|risks|budget}
    pman plan check --all
    ```
  - Flusso `plan new`:
    1. Genera template con `TemplateGenerator`
    2. Apri editor con `EditorManager.open_editor()`
    3. Avvia `FeedbackLoop.run_full()` — MAI bloccante
    4. Al completamento (o force_complete), salva con `ProjectRepository`
    5. Mostra riepilogo: blocker YAML (rossi) + warning AI (gialli) + % completezza
  - **CRITICO (Falla 2)**: `plan check --section wbs`:
    - Estrae solo la sezione WBS dal file
    - Query RAG con metadata filter (solo capitoli WBS)
    - Prompt AI ridotto → risposta < 5 secondi
  - **CRITICO (Falla 3)**: `plan check --all` analizza tutte le sezioni ma l'utente può sempre esportare
  - Output finale: file markdown in `~/.pman/projects/{name}/plan.md`
  - Test TDD: comando CLI con `CliRunner`, mock editor, test `--section`

  **Must NOT do**:
  - Non creare il progetto se l'utente esce senza salvare (editor vuoto)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: CLI user-facing, output formattato con Rich, esperienza utente importante
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD con CliRunner

  **Parallelization**:
  - **Can Run In Parallel**: NO (dipende da molti moduli Wave 2)
  - **Parallel Group**: Wave 3 (sequenziale dopo T11-T14)
  - **Blocks**: T21
  - **Blocked By**: T6 (template), T7 (editor), T11 (loop), T12 (CRUD), T13 (cloud AI)

  **References**:
  - `src/pman/cli.py` — Comandi Typer esistenti (status, models, ask)
  - `src/pman/orchestrator.py` — FeedbackLoop
  - `src/pman/templates.py` — TemplateGenerator
  - `src/pman/editor.py` — EditorManager

  **Acceptance Criteria**:
  - [ ] `pman plan new --name "Test" --editor cat` completa senza errori
  - [ ] File output salvato in `~/.pman/projects/Test/plan.md`
  - [ ] Comando mostra progresso (Rich status)
  - [ ] Test CliRunner: comando esiste, help mostra opzioni

  **QA Scenarios**:
  ```
  Scenario: Create new project via CLI
    Tool: Bash (tmux)
    Preconditions: Rich installed, template exists
    Steps:
      1. Run: EDITOR=cat pman plan new --name "MyProject" --provider ollama
      2. Assert: exit code 0
      3. Assert: output contains "Progetto MyProject creato"
      4. Check: ~/.pman/projects/MyProject/plan.md exists
    Expected Result: Project created, file saved
    Evidence: .sisyphus/evidence/task-15-new-project.txt

  Scenario: Empty editor aborts creation
    Tool: Bash
    Steps:
      1. Run: EDITOR="cp /dev/null" pman plan new --name "Empty"
      2. Assert: exit code ≠ 0 or warning "Progetto vuoto, annullato"
    Expected Result: No project created on empty save
    Evidence: .sisyphus/evidence/task-15-empty-abort.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(pman): add 'plan new' CLI command with AI-guided loop`
  - Files: `src/pman/cli.py`, `tests/test_cli_plan.py`

- [ ] 16. **`pman plan continue` Command**

  **What to do**:
  - Aggiungere sottocomando `continue`:
    ```
    pman plan continue <project_id_or_name>
    ```
  - Flusso:
    1. Carica progetto da DB via `ProjectRepository.get_by_id/name()`
    2. Recupera ultimo contenuto con `EditorManager.get_latest_content()`
    3. Apri editor con contenuto attuale
    4. Riprendi `FeedbackLoop` dall'iterazione corrente
  - Gestire: progetto non trovato, progetto già completato, nessun contenuto salvato
  - Test TDD: riprendi progetto esistente, errore su ID inesistente

  **Must NOT do**:
  - Non permettere continue su progetto con status ARCHIVED

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Load + resume pattern, logica lineare
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with T17, T18, T19)
  - **Blocks**: T21
  - **Blocked By**: T11 (loop), T12 (CRUD), T14 (errors)

  **References**:
  - `src/pman/cli.py` — Aggiungere a gruppo comandi `plan`
  - `src/pman/repository.py` — ProjectRepository
  - `src/pman/editor.py` — EditorManager.get_latest_content

  **Acceptance Criteria**:
  - [ ] `pman plan continue <id>` carica e riprende progetto
  - [ ] Errore chiaro se progetto non trovato
  - [ ] Errore se progetto già ARCHIVED
  - [ ] Test CliRunner: resume funziona, errori gestiti

  **QA Scenarios**:
  ```
  Scenario: Resume existing project
    Tool: Bash (tmux)
    Preconditions: Project "MyProject" exists with saved content
    Steps:
      1. Run: pman plan continue MyProject
      2. Assert: editor opens with saved content
      3. Assert: loop continues from last state
    Expected Result: Project loaded and resumed
    Evidence: .sisyphus/evidence/task-16-continue.txt

  Scenario: Resume non-existent project
    Tool: Bash
    Steps:
      1. Run: pman plan continue nonexistent123
      2. Assert: exit code ≠ 0, "Progetto non trovato"
    Expected Result: Clear error message
    Evidence: .sisyphus/evidence/task-16-not-found.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(pman): add 'plan continue' CLI command`
  - Files: `src/pman/cli.py`, `tests/test_cli_plan.py`

- [ ] 17. **`pman plan status` Command**

  **What to do**:
  - Aggiungere sottocomando `status`:
    ```
    pman plan status <project_id_or_name> [--force-complete]
    ```
  - Mostra tabella Rich con:
    - Nome progetto, stato (PLANNING/EXECUTION/COMPLETED)
    - Validazione YAML deterministica: errori RACI, errori Budget, errori WBS
    - Validazione AI (se disponibile): blocker e warning separati
    - Percentuale completezza per sezione
    - Iterazioni completate / 10
    - Ultimo salvataggio
  - **CRITICO (Falla 3)**: `--force-complete` marca il progetto COMPLETED indipendentemente dal validatore
  - Colori: rosso per blocker YAML, giallo per warning AI, verde per sezioni complete
  - Test TDD: progetto completo, con errori YAML, force-complete

  **Must NOT do**:
  - Non mostrare contenuto del progetto (solo metriche)
  - Non permettere modifiche da questo comando

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Display formattato Rich, query DB + validator
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: T21
  - **Blocked By**: T8 (validator), T12 (CRUD)

  **References**:
  - `src/pman/cli.py` — Pattern tabella Rich esistente (`pman status`)
  - `src/pman/validator.py` — ProjectValidator.check_completeness
  - `src/pman/repository.py` — ProjectRepository

  **Acceptance Criteria**:
  - [ ] Tabella mostra tutte le 5 sezioni con % completezza
  - [ ] Colori corretti (verde/giallo/rosso)
  - [ ] Errore chiaro se progetto non trovato

  **QA Scenarios**:
  ```
  Scenario: Status of complete project
    Tool: Bash
    Preconditions: Project with 100% completeness
    Steps:
      1. Run: pman plan status CompleteProject
      2. Assert: table shows 5/5 sections, all green
      3. Assert: "Stato: COMPLETO"
    Expected Result: 100% status, green table
    Evidence: .sisyphus/evidence/task-17-status-complete.txt

  Scenario: Status of partial project
    Tool: Bash
    Preconditions: Project with 40% completeness
    Steps:
      1. Run: pman plan status PartialProject
      2. Assert: table shows 2 green, 3 red
      3. Assert: "Completezza: 40%"
    Expected Result: Mixed colors, 40%
    Evidence: .sisyphus/evidence/task-17-status-partial.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(pman): add 'plan status' CLI command`
  - Files: `src/pman/cli.py`, `tests/test_cli_plan.py`

- [ ] 18. **`pman plan export` Command**

  **What to do**:
  - Aggiungere sottocomando `export`:
    ```
    pman plan export <project_id_or_name> [--output PATH] [--populate-db]
    ```
  - Esporta il Project Plan finale in markdown:
    - Se `--output` specificato, scrive lì
    - Altrimenti, `~/.pman/projects/{name}/plan.md`
  - Aggiunge header YAML con metadati (data, iterazioni, punteggio)
  - **CRITICO (Falla 5)**: `--populate-db` esegue un hook che:
    1. Fa il parsing dei blocchi YAML dal Markdown (RACI, WBS, Risks, Budget)
    2. Popola le tabelle `WBSTask`, `Issue`, `Risk` nel database SQLite
    3. Transizione `Project.phase` da PLANNING a EXECUTION
    4. Questo prepara il terreno per futuri comandi `pman track` / `pman update`
  - Test TDD: export con/senza --output, export con --populate-db verifica tabelle popolate, progetto non trovato

  **Must NOT do**:
  - Non esportare in PDF/HTML
  - Non forzare --populate-db (è opzionale)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Scrittura file + formattazione, logica semplice
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: T21
  - **Blocked By**: T12 (CRUD)

  **References**:
  - `src/pman/cli.py` — Aggiungere a comandi plan
  - `src/pman/repository.py` — ProjectRepository

  **Acceptance Criteria**:
  - [ ] `pman plan export <id>` produce file markdown valido
  - [ ] Header YAML contiene data e metadati
  - [ ] `--output /tmp/test.md` scrive nel path specificato
  - [ ] Warning se progetto < 100% completezza

  **QA Scenarios**:
  ```
  Scenario: Export complete project
    Tool: Bash
    Steps:
      1. Run: pman plan export CompleteProject --output /tmp/exported.md
      2. Assert: file /tmp/exported.md exists
      3. Assert: file contains all 5 section headings
      4. Assert: YAML header has date, iterations, score
    Expected Result: Valid markdown with metadata
    Evidence: .sisyphus/evidence/task-18-export.md

  Scenario: Export incomplete project warns
    Tool: Bash
    Preconditions: Project at 40% completeness
    Steps:
      1. Run: pman plan export PartialProject
      2. Assert: warning "Progetto incompleto (40%)"
      3. Assert: still exports file
    Expected Result: Warning but export succeeds
    Evidence: .sisyphus/evidence/task-18-export-warning.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(pman): add 'plan export' CLI command`
  - Files: `src/pman/cli.py`, `tests/test_cli_plan.py`

- [ ] 19. **`pman plan list` Command**

  **What to do**:
  - Aggiungere sottocomando `list`:
    ```
    pman plan list [--status {active,completed,archived,all}]
    ```
  - Mostra tabella Rich con tutti i progetti:
    - ID, Nome, Stato, Completezza %, Ultima modifica
    - Ordinati per ultima modifica (più recenti prima)
  - Filtro per stato
  - Test TDD: lista vuota, lista con progetti, filtro per stato

  **Must NOT do**:
  - Non mostrare progetti eliminati/archiviati per default (solo con `--status all`)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Query DB + tabella Rich, pattern già usato in T17
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: T21
  - **Blocked By**: T12 (CRUD)

  **References**:
  - `src/pman/cli.py` — Pattern tabella Rich
  - `src/pman/repository.py` — ProjectRepository.list_all()

  **Acceptance Criteria**:
  - [ ] `pman plan list` mostra tutti i progetti attivi
  - [ ] `pman plan list --status completed` filtra correttamente
  - [ ] Tabella ordinata per data modifica (più recente in cima)
  - [ ] Lista vuota → messaggio "Nessun progetto trovato"

  **QA Scenarios**:
  ```
  Scenario: List projects with filter
    Tool: Bash
    Preconditions: 3 projects (2 active, 1 completed)
    Steps:
      1. Run: pman plan list
      2. Assert: shows 3 projects (default includes all)
      3. Run: pman plan list --status active
      4. Assert: shows 2 projects
    Expected Result: Correct filtering
    Evidence: .sisyphus/evidence/task-19-list.txt

  Scenario: Empty list
    Tool: Bash
    Preconditions: No projects in DB
    Steps:
      1. Run: pman plan list
      2. Assert: "Nessun progetto trovato"
    Expected Result: Friendly empty message
    Evidence: .sisyphus/evidence/task-19-empty.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(pman): add 'plan list' CLI command`
  - Files: `src/pman/cli.py`, `tests/test_cli_plan.py`

- [ ] 20. **CLI Integration + Refactoring**

  **What to do**:
  - Refactoring dei comandi CLI esistenti:
    - Spostare comandi `plan` in `src/pman/commands/plan.py`
    - Aggiornare `src/pman/cli.py` per importare da commands/
  - Aggiungere help text dettagliato per ogni comando
  - Aggiungere `--verbose` flag globale per debug logging
  - Verificare che `pman status` funzioni con i nuovi moduli
  - Rendere async i comandi CLI che chiamano moduli async (usando `asyncio.run()`)
  - Test CliRunner: tutti i comandi accessibili, help mostra tutte le opzioni

  **Must NOT do**:
  - Non rimuovere comandi esistenti (status, models, repos, ask)
  - Non cambiare interfaccia pubblica dei comandi esistenti

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Refactoring + integrazione, pattern già stabiliti
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: NO (dipende da T15-T19)
  - **Parallel Group**: Wave 3 (finale wave)
  - **Blocks**: T21
  - **Blocked By**: T15, T16, T17, T18, T19

  **References**:
  - `src/pman/cli.py` — Comandi esistenti da preservare
  - `src/pman/commands/plan.py` — Nuovi comandi plan

  **Acceptance Criteria**:
  - [ ] `pman --help` mostra tutti i comandi (status, models, repos, ask, plan)
  - [ ] `pman plan --help` mostra tutti i sottocomandi
  - [ ] Comandi esistenti (status, models) funzionano invariati
  - [ ] `pman --verbose plan new` mostra log di debug

  **QA Scenarios**:
  ```
  Scenario: CLI help shows all commands
    Tool: Bash
    Steps:
      1. Run: pman --help
      2. Assert: output contains "status", "models", "repos", "ask", "plan"
      3. Run: pman plan --help
      4. Assert: output contains "new", "continue", "status", "export", "list"
    Expected Result: Complete help text
    Evidence: .sisyphus/evidence/task-20-help.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `refactor(pman): integrate plan commands and reorganize CLI`
  - Files: `src/pman/cli.py`, `src/pman/commands/__init__.py`, `src/pman/commands/plan.py`

- [ ] 21. **End-to-End Integration Tests**

  **What to do**:
  - Creare `tests/test_e2e.py`:
    - Test `test_full_workflow_new_project`: `pman plan new` → editor → loop → export
    - Test `test_resume_and_complete`: new → interrompi → continue → completa
    - Test `test_degradation_no_ai`: workflow senza AI disponibile
    - Test `test_degradation_no_rag`: workflow senza PDF dispensa
  - Usare `EDITOR=cat` con input predefiniti per test deterministici
  - Mockare AI provider per output prevedibili
  - Test TDD: ogni scenario ha input atteso e output verificabile

  **Must NOT do**:
  - Non testare con Ollama reale in CI (solo mock)
  - Non scrivere test che richiedono rete

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Orchestrazione multi-modulo, setup complesso, mock multipli
  - **Skills**: [`testing`]
    - `testing`: Pattern E2E test, fixtures, mocking strategies

  **Parallelization**:
  - **Can Run In Parallel**: NO (dipende da Wave 3)
  - **Parallel Group**: Wave 4 (sequenziale dopo Wave 3)
  - **Blocks**: F1-F4
  - **Blocked By**: T15-T19 (all CLI), T1 (test infra)

  **References**:
  - `tests/conftest.py` — Fixtures esistenti
  - `tests/test_cli_plan.py` — Pattern CliRunner
  - `src/pman/orchestrator.py` — FeedbackLoop

  **Acceptance Criteria**:
  - [ ] `test_full_workflow` passa con mock AI
  - [ ] `test_degradation_no_ai` verifica graceful degradation
  - [ ] `test_degradation_no_rag` verifica funzionamento senza dispensa
  - [ ] `pytest tests/test_e2e.py -v` → tutti i test E2E passano

  **QA Scenarios**:
  ```
  Scenario: Full workflow from new to export
    Tool: Bash (pytest)
    Preconditions: All mocks configured, template exists
    Steps:
      1. Run: pytest tests/test_e2e.py::test_full_workflow_new_project -v
      2. Assert: test passes
      3. Verify: exported file has all 5 sections
    Expected Result: Complete workflow succeeds
    Evidence: .sisyphus/evidence/task-21-e2e.txt

  Scenario: Workflow without RAG
    Tool: Bash (pytest)
    Steps:
      1. Run: pytest tests/test_e2e.py::test_degradation_no_rag -v
      2. Assert: test passes, no crash
      3. Assert: output file created (structure-only feedback)
    Expected Result: Works without textbook
    Evidence: .sisyphus/evidence/task-21-no-rag.txt
  ```

  **Commit**: YES (groups with Wave 4)
  - Message: `test(pman): add end-to-end integration tests`
  - Files: `tests/test_e2e.py`

- [ ] 22. **Session Recovery (Temp File Preservation)**

  **What to do**:
  - Implementare `SessionRecovery` in `src/pman/editor.py`:
    - `save_checkpoint(project_id, content)` — salva ogni N minuti (configurabile)
    - `detect_crash(project_id) -> bool` — verifica se file temporaneo esiste senza processo attivo
    - `offer_recovery(project_id) -> str | None` — all'avvio, se crash rilevato, chiedi "Ripristinare?"
  - Integrare in `pman plan new` e `pman plan continue`:
    - All'avvio, verifica crash
    - Durante il loop, checkpoint automatico
  - Test TDD: crash simulato, recovery offerto, recovery rifiutato

  **Must NOT do**:
  - Non sovrascrivere automaticamente senza conferma
  - Non salvare checkpoint se il contenuto non è cambiato

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: File system + recovery logic, pattern ben definito
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with T23, T24)
  - **Blocks**: None
  - **Blocked By**: T7 (editor), T14 (errors)

  **References**:
  - `src/pman/editor.py` — EditorManager, snapshots
  - `src/pman/config.py` — Aggiungere `checkpoint_interval` setting

  **Acceptance Criteria**:
  - [ ] Crash detection funziona (file temp senza lock)
  - [ ] Recovery offer mostra contenuto recuperabile
  - [ ] Checkpoint automatico ogni N minuti durante il loop
  - [ ] Test: crash → recovery → ripristino ok

  **QA Scenarios**:
  ```
  Scenario: Crash recovery offered
    Tool: Bash
    Preconditions: Stale temp file exists from previous session
    Steps:
      1. Run: pman plan new --name TestProject
      2. Assert: prompt "Sessione precedente non chiusa. Ripristinare? [y/N]"
      3. Answer: y
      4. Assert: editor opens with recovered content
    Expected Result: Recovery works
    Evidence: .sisyphus/evidence/task-22-recovery.txt

  Scenario: Recovery declined
    Tool: Bash
    Steps:
      1. Run: pman plan new --name TestProject
      2. Assert: recovery prompt
      3. Answer: n
      4. Assert: starts fresh with template
    Expected Result: Fresh start on decline
    Evidence: .sisyphus/evidence/task-22-decline.txt
  ```

  **Commit**: YES (groups with Wave 4)
  - Message: `feat(pman): add session recovery from temp files`
  - Files: `src/pman/editor.py`, `tests/test_editor.py`

- [ ] 23. **Performance Optimization (Caching, Lazy Loading)**

  **What to do**:
  - Ottimizzare embedding: cache su disco (pickle) dei chunk processati
  - Ottimizzare ChromaDB: non ricaricare da zero se collection esiste
  - Lazy loading: PDF processato solo al primo utilizzo, non all'import
  - Aggiungere progress bar (Rich) per operazioni lunghe (PDF→embedding: ~30-60s)
  - Test: inizializzazione prima vs seconda (seconda < 1s)

  **Must NOT do**:
  - Non precaricare tutto all'avvio del CLI
  - Non usare multiprocessing

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Ottimizzazione performance, caching strategies
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocks**: None
  - **Blocked By**: T21 (E2E tests)

  **References**:
  - `src/pman/vector_store.py` — ChromaDB integration
  - `src/pman/embedder.py` — Embedding pipeline
  - `src/pman/rag.py` — RAG pipeline

  **Acceptance Criteria**:
  - [ ] Primo avvio: ~30-60s per processare PDF
  - [ ] Secondo avvio: < 1s (cache hit)
  - [ ] Progress bar visibile durante processing
  - [ ] Nessun caricamento eager all'import del modulo

  **QA Scenarios**:
  ```
  Scenario: Second initialization is fast
    Tool: Bash
    Preconditions: First initialization completed
    Steps:
      1. Time first pman plan new (cold)
      2. Time second pman plan new (warm)
      3. Assert: warm time < 2s
    Expected Result: Near-instant second run
    Evidence: .sisyphus/evidence/task-23-cache-speed.txt

  Scenario: Progress bar during PDF processing
    Tool: Bash (tmux)
    Steps:
      1. Delete cache, run pman plan new --name FastTest
      2. Assert: progress bar shown during "Elaborazione dispensa..."
    Expected Result: Progress feedback
    Evidence: .sisyphus/evidence/task-23-progress.txt
  ```

  **Commit**: YES (groups with Wave 4)
  - Message: `perf(pman): add caching and lazy loading for RAG pipeline`
  - Files: `src/pman/vector_store.py`, `src/pman/embedder.py`, `src/pman/rag.py`

- [ ] 24. **Refactoring: Remove Dead Code, Align Imports**

  **What to do**:
  - Rimuovere endpoint API stub che non servono più (focus solo CLI)
  - Rendere async `ollama.py` (sostituire urllib con httpx.AsyncClient)
  - Fixare bug token vuoto in `github.py`
  - Aggiungere type hints mancanti
  - Verificare `ruff check .` → 0 errori
  - Verificare `pytest tests/ -v --cov=src/pman` → tutti passano, coverage ≥ 80%

  **Must NOT do**:
  - Non rimuovere github.py (serve per comandi esistenti)
  - Non cambiare API pubblica di config.py

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pulizia e refactoring, pattern già noti
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `testing`: TDD

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4
  - **Blocks**: None
  - **Blocked By**: T21 (E2E tests)

  **References**:
  - `src/pman/ollama.py` — Da rendere async
  - `src/pman/github.py` — Bug token vuoto
  - `src/pman/api.py` — Endpoint stub da valutare

  **Acceptance Criteria**:
  - [ ] `ruff check src/pman/` → 0 errori
  - [ ] `pytest tests/ --cov=src/pman --cov-report=term` → coverage ≥ 80%
  - [ ] `ollama.py` usa `httpx.AsyncClient`
  - [ ] `github.py` gestisce token vuoto

  **QA Scenarios**:
  ```
  Scenario: Lint and coverage pass
    Tool: Bash
    Steps:
      1. Run: ruff check src/pman/
      2. Assert: exit code 0, 0 errors
      3. Run: pytest tests/ --cov=src/pman --cov-report=term --cov-fail-under=80
      4. Assert: exit code 0, coverage ≥ 80%
    Expected Result: Clean lint, good coverage
    Evidence: .sisyphus/evidence/task-24-lint-coverage.txt

  Scenario: Async Ollama client works
    Tool: Bash (python -c)
    Preconditions: Ollama running
    Steps:
      1. Run: from pman.ollama import OllamaClient; import asyncio; asyncio.run(OllamaClient().list_models())
      2. Assert: returns list of models without error
    Expected Result: Async client functional
    Evidence: .sisyphus/evidence/task-24-async-ollama.txt
  ```

  **Commit**: YES (groups with Wave 4)
  - Message: `refactor(pman): async ollama, fix bugs, align imports, clean stubs`
  - Files: `src/pman/ollama.py`, `src/pman/github.py`, `src/pman/api.py`

- [ ] 25. **`pman backup` Command (Portabilità Workspace)**

  **What to do**:
  - Aggiungere comando `backup` a `src/pman/cli.py`:
    ```
    pman backup [--dest /path/to/save] [--restore /path/to/archive.zip]
    ```
  - **CRITICO (Backup/Portabilità)**: `pman backup --dest /backup/path`:
    - Comprime l'intera cartella `~/.pman/` (DB SQLite, ChromaDB, progetti markdown, config) in un archivio ZIP
    - Include `.env` (senza API key, sostituite con `***`)
    - Nomina l'archivio: `pman-backup-YYYYMMDD-HHMMSS.zip`
    - Mostra dimensione archivio e file contenuti
  - `pman backup --restore /path/to/archive.zip`:
    - Estrae l'archivio in `~/.pman/`
    - Verifica integrità (DB non corrotto, ChromaDB compatibile)
    - Chiede conferma prima di sovrascrivere
  - Test TDD: backup crea archivio valido, restore funziona, restore rifiuta archivio corrotto

  **Must NOT do**:
  - Non includere API key in chiaro nell'archivio
  - Non sovrascrivere senza conferma

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Compressione file system + verifica integrità
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with CLI commands)
  - **Blocks**: None
  - **Blocked By**: T12 (CRUD per conoscere struttura dati)

  **References**:
  - `src/pman/config.py` — `projects_dir`, `chroma_path`, `db_path` settings
  - `src/pman/cli.py` — Pattern comandi Typer

  **Acceptance Criteria**:
  - [ ] `pman backup --dest /tmp/` crea archivio ZIP > 0 bytes
  - [ ] Archivio contiene: `pman.db`, `chromadb/`, `projects/`, `.env` (sanitized)
  - [ ] `pman backup --restore /tmp/pman-backup.zip` ripristina workspace
  - [ ] Archivio corrotto → errore chiaro, nessun ripristino parziale

  **QA Scenarios**:
  ```
  Scenario: Backup creates valid archive
    Tool: Bash
    Preconditions: At least 1 project exists
    Steps:
      1. Run: pman backup --dest /tmp/
      2. Assert: file created matching pman-backup-*.zip
      3. Assert: file size > 0
      4. Run: unzip -l /tmp/pman-backup-*.zip
      5. Assert: contains pman.db, chromadb/, projects/
    Expected Result: Complete workspace archive
    Evidence: .sisyphus/evidence/task-25-backup.txt

  Scenario: Restore recovers workspace
    Tool: Bash
    Preconditions: Backup archive exists, ~/.pman/ deleted
    Steps:
      1. Delete ~/.pman/
      2. Run: pman backup --restore /tmp/pman-backup-*.zip
      3. Assert: ~/.pman/ restored with all files
      4. Run: pman plan list
      5. Assert: projects visible again
    Expected Result: Full workspace recovery
    Evidence: .sisyphus/evidence/task-25-restore.txt
  ```

  **Commit**: YES (groups with Wave 3)
  - Message: `feat(pman): add backup/restore command for workspace portability`
  - Files: `src/pman/cli.py`, `tests/test_cli_backup.py`

- [ ] 26. **CI/CD GitHub Actions Workflow**

  **What to do**:
  - Creare `.github/workflows/test.yml`:
    ```yaml
    name: Test & Lint
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            python-version: ["3.12"]
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: ${{ matrix.python-version }}
          - run: pip install -e ".[dev]"
          - run: ruff check src/pman/
          - run: pytest tests/ -v --cov=src/pman --cov-fail-under=80
    ```
  - **CRITICO (CI/CD)**: Garantisce che ogni push/PR esegua automaticamente:
    - Linting con ruff
    - Suite di test con coverage ≥ 80%
    - Blocco merge se i test falliscono
  - Aggiungere badge nel README: `[![CI](https://github.com/BigBoss133/SMOT-PMANAGER/actions/workflows/test.yml/badge.svg)]`
  - Test: verifica manuale che la workflow parta su push

  **Must NOT do**:
  - Non eseguire test che richiedono Ollama (solo mock)
  - Non caricare API key reali nei secrets (per ora)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: File YAML standard GitHub Actions
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (con altri task di setup)
  - **Blocks**: None
  - **Blocked By**: None (indipendente)

  **References**:
  - `pyproject.toml` — Dipendenze dev (ruff, pytest, pytest-cov)
  - GitHub Actions docs: `setup-python`, `actions/checkout`

  **Acceptance Criteria**:
  - [ ] `.github/workflows/test.yml` esiste con sintassi YAML valida
  - [ ] Push attiva la workflow su GitHub Actions
  - [ ] Workflow esegue `ruff check` e `pytest`
  - [ ] Badge CI nel README

  **QA Scenarios**:
  ```
  Scenario: Workflow triggers on push
    Tool: GitHub Actions UI
    Preconditions: Workflow file committed and pushed
    Steps:
      1. Push any commit to main
      2. Navigate to Actions tab on GitHub
      3. Assert: workflow "Test & Lint" is running
      4. Wait for completion
      5. Assert: all jobs pass (green checkmark)
    Expected Result: CI passes automatically
    Evidence: .sisyphus/evidence/task-26-ci-passed.png
  ```

  **Commit**: YES (groups with Wave 1)
  - Message: `ci: add GitHub Actions workflow for lint + test`
  - Files: `.github/workflows/test.yml`, `README.md`

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Leggi il piano end-to-end. Verifica ogni "Must Have": esiste implementazione? Ogni "Must NOT Have": cerca pattern proibiti. Verifica evidence files in `.sisyphus/evidence/`.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Esegui `ruff check . && mypy src/pman/ && pytest`. Verifica: `as any`/`@ts-ignore`, catch vuoti, print di debug, codice commentato, import inutilizzati. Controlla AI slop: commenti eccessivi, over-abstraction, nomi generici.
  Output: `Lint [PASS/FAIL] | Type [PASS/FAIL] | Tests [N pass/N fail] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Parti da stato pulito. Esegui TUTTI gli scenari QA di ogni task. Testa integrazione cross-task (nuovo progetto → edit → AI feedback → export). Testa edge case: file vuoto, Ollama spento, PDF mancante.
  Evidenza in `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  Per ogni task: leggi "What to do", leggi diff effettivo. Verifica 1:1 — tutto ciò che era specificato è stato costruito, nulla oltre lo scope. Controlla "Must NOT do" compliance. Verifica contaminazione cross-task.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat(pman): add test infra, PyMuPDF extraction with metadata, RAG pipeline, cross-OS editor, CI/CD` — T1-T7, T26
- **Wave 2**: `feat(pman): add YAML validator, RAG metadata filter, AI feedback blockers/warnings, orchestrator advisory mode, CRUD expanded models, Ollama circuit breaker` — T8-T14
- **Wave 3**: `feat(pman): add plan CLI (new/check --section/continue/status --force-complete/export --populate-db/list/backup)` — T15-T20, T25
- **Wave 4**: `feat(pman): add E2E tests, session recovery, cache, async refactor` — T21-T24
- **FINAL**: `chore(pman): final verification and cleanup` — F1-F4

---

## Success Criteria

### Verification Commands
```bash
# Test suite
pytest tests/ -v
# Expected: all tests pass, coverage ≥ 80%

# CLI smoke test
pman plan new --name "Test Project" --editor cat
# Expected: editor opens, template with YAML blocks

# Section-based check (Falla 2)
pman plan check --section wbs
# Expected: response < 5s, solo contesto WBS

# Force complete (Falla 3)
pman plan status <id> --force-complete
# Expected: progetto marcato COMPLETED

# Export with DB population (Falla 5)
pman plan export <id> --populate-db
# Expected: tabelle WBSTask, Issue, Risk popolate

# YAML validation (Falla 1)
# Inserire RACI con 2 Accountable → il validatore deve segnalare errore
```

### Final Checklist
- [ ] Tutti i "Must Have" presenti
- [ ] Tutti i "Must NOT Have" assenti
- [ ] Tutti i test passano, coverage ≥ 80%
- [ ] RAG metadata filter: query WBS → solo chunk Capitoli 13-14
- [ ] YAML validator rileva 2 Accountable nella stessa riga RACI
- [ ] AI feedback separa blocker (rossi) da warning (gialli)
- [ ] `plan check --section` risponde in < 5 secondi
- [ ] `plan status --force-complete` funziona come override
- [ ] `plan export --populate-db` popola WBSTask, Issue, Risk
- [ ] AI funziona sia con Ollama che con API cloud
- [ ] Loop feedback mai bloccante (utente può sempre esportare)
