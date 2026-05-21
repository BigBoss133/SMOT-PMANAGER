from dataclasses import dataclass, field
from typing import Optional

from pman.config import settings
from pman.rag import RAGContext, RAGPipeline
from pman.validator import CompletenessReport


@dataclass
class FeedbackItem:
    section: str
    severity: str
    message: str
    suggestion: str = ""


@dataclass
class FeedbackReport:
    items: list[FeedbackItem] = field(default_factory=list)
    can_export: bool = True
    overall_score: int = 0


class AIFeedbackGenerator:
    def __init__(self, rag_pipeline: RAGPipeline | None = None):
        self.rag = rag_pipeline or RAGPipeline()

    def generate_feedback(
        self,
        section_name: str,
        section_content: str,
        completeness: CompletenessReport,
    ) -> FeedbackReport:
        report = FeedbackReport()
        report.overall_score = completeness.overall_score

        for error in completeness.yaml_errors:
            report.items.append(FeedbackItem(
                section=section_name,
                severity="blocker",
                message=error,
            ))

        for warning in completeness.text_warnings:
            report.items.append(FeedbackItem(
                section=section_name,
                severity="warning",
                message=warning,
            ))

        if section_content and len(section_content.split()) > 10:
            try:
                rag_context = self.rag.query_section(section_name, section_content[:500])
                if rag_context.chunks:
                    report.items.append(FeedbackItem(
                        section=section_name,
                        severity="info",
                        message=f"Found {len(rag_context.chunks)} relevant textbook passages",
                        suggestion="Review these passages for best practices",
                    ))
            except Exception:
                pass

        return report
