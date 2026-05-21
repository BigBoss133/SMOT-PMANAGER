import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pman.editor import EditorManager
from pman.feedback import AIFeedbackGenerator, FeedbackReport
from pman.templates import TemplateGenerator
from pman.validator import CompletenessReport, ProjectValidator


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

    def run_loop(
        self,
        project_name: str,
        initial_content: Optional[str] = None,
    ) -> LoopResult:
        result = LoopResult()
        content = initial_content or self.template.generate(project_name)

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            result.iterations = iteration

            content = self.editor.open_editor(content, project_name)
            if not content.strip():
                break

            self.editor.save_snapshot(content, project_name, iteration)

            completeness = self.validator.check_completeness(content)

            sections = self.validator.parse_sections(content)
            for section_name, section_text in sections.items():
                report = self.feedback.generate_feedback(
                    section_name, section_text, completeness
                )
                result.feedback_reports.append(report)

            if self._user_wants_to_exit(content):
                result.completed = True
                break

        result.final_content = content
        return result

    def _user_wants_to_exit(self, content: str) -> bool:
        return "<!-- DONE -->" in content or "# DONE" in content

    def check_section(self, project_name: str, section: str) -> FeedbackReport:
        content = self.editor.get_latest_content(project_name) or ""
        sections = self.validator.parse_sections(content)
        section_text = sections.get(section, "")
        completeness = self.validator.check_completeness(content)
        return self.feedback.generate_feedback(section, section_text, completeness)
