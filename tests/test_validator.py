
from pman.validator import ProjectValidator


class TestParseSections:
    def test_finds_all_sections(self):
        validator = ProjectValidator()
        content = """
## Project Charter
Some charter text here with enough words to pass.

## Stakeholder Analysis & RACI Matrix
Stakeholder analysis text goes here.

## Work Breakdown Structure & Schedule
WBS description.

## Risk Analysis
Risk text.

## Budget & Cost Estimation
Budget text.
"""
        sections = validator.parse_sections(content)
        assert len(sections) == 5
        assert "Project Charter" in sections
        assert len(sections["Project Charter"]) > 0

    def test_missing_section(self):
        validator = ProjectValidator()
        sections = validator.parse_sections("## Project Charter\nText here.")
        assert sections["Risk Analysis"] == ""


class TestParseYamlBlocks:
    def test_extracts_raci(self):
        validator = ProjectValidator()
        content = """
# BEGIN RACI
raci_matrix:
  - task: "Test"
    responsible: "Dev"
    accountable: "PM"
# END RACI
"""
        blocks = validator.parse_yaml_blocks(content)
        assert "raci" in blocks
        assert blocks["raci"]["raci_matrix"][0]["task"] == "Test"

    def test_missing_block(self):
        validator = ProjectValidator()
        blocks = validator.parse_yaml_blocks("no blocks here")
        assert blocks["raci"] == {}


class TestValidateRaci:
    def test_valid_raci(self):
        validator = ProjectValidator()
        data = {"raci_matrix": [{"responsible": "Dev", "accountable": "PM"}]}
        assert validator.validate_raci(data) == []

    def test_missing_accountable(self):
        validator = ProjectValidator()
        data = {"raci_matrix": [{"responsible": "Dev"}]}
        errors = validator.validate_raci(data)
        assert any("Accountable" in e for e in errors)


class TestValidateBudget:
    def test_balanced_budget(self):
        validator = ProjectValidator()
        data = {"budget": {"items": [{"estimated_cost": 100}], "total": 100}}
        assert validator.validate_budget(data) == []

    def test_mismatch(self):
        validator = ProjectValidator()
        data = {"budget": {"items": [{"estimated_cost": 100}], "total": 200}}
        errors = validator.validate_budget(data)
        assert len(errors) == 1


class TestCheckCompleteness:
    def test_full_content(self):
        validator = ProjectValidator()
        content = ""
        for section in validator.get_sections():
            content += f"## {section}\n" + "word " * 60 + "\n"
        report = validator.check_completeness(content)
        assert report.overall_score == 100

    def test_empty_content(self):
        validator = ProjectValidator()
        report = validator.check_completeness("")
        assert report.overall_score == 0
        assert len(report.missing_sections) == 5
