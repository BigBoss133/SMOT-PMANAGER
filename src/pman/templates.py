from pathlib import Path


class TemplateGenerator:
    TEMPLATE_DIR = Path(__file__).parent / "templates"

    def generate(self, project_name: str = "") -> str:
        path = self.TEMPLATE_DIR / "project_plan.md"
        content = path.read_text(encoding="utf-8")
        if project_name:
            content = content.replace("{{PROJECT_NAME}}", project_name)
        return content

    def get_sections(self) -> list[str]:
        return [
            "Project Charter",
            "Stakeholder Analysis & RACI Matrix",
            "Work Breakdown Structure & Schedule",
            "Risk Analysis",
            "Budget & Cost Estimation",
        ]

    def get_yaml_blocks(self) -> list[str]:
        return ["RACI", "WBS", "RISKS", "BUDGET"]
