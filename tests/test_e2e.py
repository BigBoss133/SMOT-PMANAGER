"""End-to-end tests: full user flow from creation to export."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from pman.bundle import BundleGenerator
from pman.editor import EditorManager
from pman.models import Base
from pman.orchestrator import FeedbackOrchestrator
from pman.rag import RAGContext
from pman.repository import ProjectRepository
from pman.templates import TemplateGenerator
from pman.validator import ProjectValidator


@pytest.fixture
async def async_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


class TestFullUserFlow:
    @pytest.mark.asyncio
    async def test_create_analyze_export(self, async_db_session):
        """Simulate: create project -> edit -> AI feedback -> export bundle."""
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            "os.environ", {"PMAN_PROJECTS_DIR": tmp, "EDITOR": "cat"}
        ):
            # 1. Create project
            repo = ProjectRepository(async_db_session)
            project = await repo.create_project("e2e-full")
            assert project.id is not None

            # 2. Generate template and "edit"
            template = TemplateGenerator()
            content = template.generate("e2e-full")
            assert "## Project Charter" in content

            editor = EditorManager(tmp)
            edited = editor.open_editor(content, "e2e-full")
            assert "Project Charter" in edited
            assert editor.has_recovery("e2e-full") is False  # cat clears recovery

            # 3. AI feedback loop (mock RAG)
            orchestrator = FeedbackOrchestrator()
            orchestrator.rag = MagicMock()
            orchestrator.rag.query_section.return_value = RAGContext(
                question="", chunks=[]
            )

            result = await orchestrator.run_loop(
                "e2e-full", initial_content=edited, start_iteration=1
            )
            assert result.iterations >= 1
            assert result.final_content != ""
            assert len(result.feedback_reports) > 0

            # 4. Validate completeness
            validator = ProjectValidator()
            report = validator.check_completeness(result.final_content)
            assert report.overall_score >= 0

            # 5. Export bundle
            generator = BundleGenerator(
                "e2e-full", result.final_content, Path(tmp) / "e2e-full"
            )
            excel_path = generator.generate_excel()
            email_path = generator.generate_email()
            assert excel_path.exists()
            assert email_path.exists()

            # 6. Verify email contains project name
            email_text = email_path.read_text()
            assert "e2e-full" in email_text

    @pytest.mark.asyncio
    async def test_session_recovery(self, async_db_session):
        """Simulate crash recovery: auto-save exists and is restored."""
        with tempfile.TemporaryDirectory() as tmp:
            editor = EditorManager(tmp)
            editor.save_autorecovery("recovered content", "crash-test")
            assert editor.has_recovery("crash-test") is True

            recovered = editor.recover("crash-test")
            assert recovered == "recovered content"

            editor.clear_recovery("crash-test")
            assert editor.has_recovery("crash-test") is False

    def test_lazy_vector_store(self):
        """Vector store skips PDF reprocessing when already initialized."""
        with tempfile.TemporaryDirectory() as tmp:
            from pman.vector_store import VectorStore

            store = VectorStore(chroma_path=tmp, collection_name="lazy_test")
            # Empty store is not initialized
            assert store.is_initialized() is False

            # Manually add a dummy document to simulate prior initialization
            store.add_documents(
                [type("C", (), {"text": "dummy", "chapter_number": 1, "topic": "wbs"})()],
                [[0.1] * 768],
            )
            assert store.is_initialized() is True

            # Second call should be a no-op due to lazy check
            store.initialize_from_pdf(pdf_path="/nonexistent/path.pdf")
            assert store.is_initialized() is True
