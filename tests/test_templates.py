
from pman.templates import TemplateGenerator


class TestTemplateGenerator:
    def test_generate_returns_string(self):
        gen = TemplateGenerator()
        result = gen.generate()
        assert isinstance(result, str)
        assert len(result) > 1000

    def test_generate_replaces_project_name(self):
        gen = TemplateGenerator()
        result = gen.generate("My Project")
        assert "My Project" in result

    def test_all_sections_present(self):
        gen = TemplateGenerator()
        result = gen.generate()
        assert "# Project Charter" in result
        assert "# Stakeholder Analysis & RACI Matrix" in result
        assert "# Work Breakdown Structure & Schedule" in result
        assert "# Risk Analysis" in result
        assert "# Budget & Cost Estimation" in result

    def test_yaml_blocks_present(self):
        gen = TemplateGenerator()
        result = gen.generate()
        assert "# BEGIN RACI" in result
        assert "# END RACI" in result
        assert "# BEGIN WBS" in result
        assert "# END WBS" in result
        assert "# BEGIN RISKS" in result
        assert "# END RISKS" in result
        assert "# BEGIN BUDGET" in result
        assert "# END BUDGET" in result

    def test_get_sections_returns_five(self):
        gen = TemplateGenerator()
        sections = gen.get_sections()
        assert len(sections) == 5
        assert "Project Charter" in sections

    def test_get_yaml_blocks_returns_four(self):
        gen = TemplateGenerator()
        blocks = gen.get_yaml_blocks()
        assert len(blocks) == 4
        assert "RACI" in blocks
        assert "WBS" in blocks
        assert "RISKS" in blocks
        assert "BUDGET" in blocks
