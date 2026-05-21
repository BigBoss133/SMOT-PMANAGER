
from pman.feedback import AIFeedbackGenerator, FeedbackReport
from pman.validator import CompletenessReport


class TestAIFeedbackGenerator:
    def test_generate_feedback_with_errors(self):
        gen = AIFeedbackGenerator()
        completeness = CompletenessReport(
            overall_score=50,
            yaml_errors=["Missing Accountable"],
            text_warnings=["Low word count"],
        )
        report = gen.generate_feedback("WBS", "Some text here", completeness)
        assert isinstance(report, FeedbackReport)
        assert report.overall_score == 50
        assert any(item.severity == "blocker" for item in report.items)
        assert any(item.severity == "warning" for item in report.items)

    def test_advisory_mode_never_blocks(self):
        gen = AIFeedbackGenerator()
        completeness = CompletenessReport(
            overall_score=0,
            yaml_errors=["Error"],
        )
        report = gen.generate_feedback("WBS", "", completeness)
        assert report.can_export is True

    def test_empty_content(self):
        gen = AIFeedbackGenerator()
        completeness = CompletenessReport(overall_score=0)
        report = gen.generate_feedback("WBS", "", completeness)
        assert report.overall_score == 0
