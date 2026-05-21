import tempfile
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from pman.editor import EditorManager
from pman.models import Base
from pman.orchestrator import FeedbackOrchestrator
from pman.repository import ProjectRepository
from pman.templates import TemplateGenerator
from pman.validator import ProjectValidator


class TestEndToEndFlow:
    @pytest.mark.asyncio
    async def test_create_edit_validate_export(self):
        tmp = tempfile.mkdtemp()

        with patch.dict("os.environ", {"PMAN_PROJECTS_DIR": tmp, "EDITOR": "cat"}):
            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            Session = async_sessionmaker(engine, expire_on_commit=False)
            async with Session() as session:
                repo = ProjectRepository(session)
                project = await repo.create_project("e2e-test")

                template = TemplateGenerator()
                content = template.generate("e2e-test")

                editor = EditorManager()
                result = editor.open_editor(content, "e2e-test")
                assert "Project Charter" in result

                editor.save_snapshot(result, "e2e-test", 1)
                latest = editor.get_latest_content("e2e-test")
                assert latest is not None
                assert "Project Charter" in latest

                validator = ProjectValidator()
                report = validator.check_completeness(latest)
                assert report.overall_score >= 0

                sections = validator.parse_sections(latest)
                assert len(sections) == 5

                blocks = validator.parse_yaml_blocks(latest)
                assert "raci" in blocks

            await engine.dispose()

    @pytest.mark.asyncio
    async def test_orchestrator_loop(self):
        tmp = tempfile.mkdtemp()

        with patch.dict("os.environ", {"EDITOR": "cat", "PMAN_PROJECTS_DIR": tmp}):
            orchestrator = FeedbackOrchestrator()

            content = "## Project Charter\n" + "word " * 60 + "\n"
            content += "## Stakeholder Analysis & RACI Matrix\n" + "word " * 60 + "\n"
            content += "## Work Breakdown Structure & Schedule\n" + "word " * 60 + "\n"
            content += "## Risk Analysis\n" + "word " * 60 + "\n"
            content += "## Budget & Cost Estimation\n" + "word " * 60 + "\n"

            result = await orchestrator.run_loop("e2e-loop", initial_content=content)
            assert result.iterations >= 1
            assert result.final_content != ""

    def test_template_to_validation(self):
        template = TemplateGenerator()
        content = template.generate("validation-test")

        validator = ProjectValidator()
        report = validator.check_completeness(content)

        assert report.overall_score >= 0

        sections = validator.parse_sections(content)
        assert len(sections) == 5

        blocks = validator.parse_yaml_blocks(content)
        assert "raci" in blocks
        assert "wbs" in blocks
        assert "risks" in blocks
        assert "budget" in blocks
