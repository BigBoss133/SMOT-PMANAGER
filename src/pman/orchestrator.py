import asyncio
from dataclasses import dataclass, field

from pman.editor import EditorManager
from pman.feedback import AIFeedbackGenerator, FeedbackReport
from pman.rag import RAGPipeline
from pman.templates import TemplateGenerator
from pman.validator import ProjectValidator


@dataclass
class LoopResult:
    completed: bool = False
    iterations: int = 0
    final_content: str = ""
    feedback_reports: list[FeedbackReport] = field(default_factory=list)


class FeedbackOrchestrator:
    MAX_ITERATIONS = 10

    def __init__(self):
        self.editor = EditorManager()
        self.validator = ProjectValidator()
        self.feedback = AIFeedbackGenerator()
        self.template = TemplateGenerator()
        self.rag = RAGPipeline()

    async def run_loop(
        self,
        project_name: str,
        initial_content: str | None = None,
        start_iteration: int = 1,
    ) -> LoopResult:
        result = LoopResult()
        content = initial_content or self.template.generate(project_name)

        for iteration in range(start_iteration, self.MAX_ITERATIONS + 1):
            result.iterations = iteration

            content = await asyncio.to_thread(
                self.editor.open_editor, content, project_name
            )
            if not content.strip():
                break

            await asyncio.to_thread(
                self.editor.save_snapshot, content, project_name, iteration
            )

            completeness = self.validator.check_completeness(content)

            sections = self.validator.parse_sections(content)
            for section_name, section_text in sections.items():
                rag_context = await asyncio.to_thread(
                    self.rag.query_section, section_name, section_text[:500]
                )
                report = await asyncio.to_thread(
                    self.feedback.generate_feedback,
                    section_name,
                    section_text,
                    completeness,
                    rag_context,
                )
                result.feedback_reports.append(report)

            if self._user_wants_to_exit(content):
                result.completed = True
                break

        result.final_content = content
        return result

    def _user_wants_to_exit(self, content: str) -> bool:
        return "<!-- DONE -->" in content or "# DONE" in content

    async def check_section(
        self, project_name: str, section: str
    ) -> FeedbackReport:
        content = await asyncio.to_thread(
            self.editor.get_latest_content, project_name
        )
        content = content or ""
        sections = self.validator.parse_sections(content)
        section_text = sections.get(section, "")
        completeness = self.validator.check_completeness(content)
        rag_context = await asyncio.to_thread(
            self.rag.query_section, section, section_text[:500]
        )
        return await asyncio.to_thread(
            self.feedback.generate_feedback,
            section,
            section_text,
            completeness,
            rag_context,
        )
