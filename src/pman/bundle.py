"""Bundle generator: Excel workbook + Sponsor email from validated YAML blocks."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from pman.validator import ProjectValidator


class BundleGenerator:
    """Generates a project artifact bundle (Excel + email) from plan content."""

    def __init__(self, project_name: str, content: str, output_dir: Path):
        self.project_name = project_name
        self.content = content
        self.output_dir = output_dir
        self.validator = ProjectValidator()
        self.blocks = self.validator.parse_yaml_blocks(content)

    def generate_excel(self) -> Path:
        """Create project_artifacts.xlsx with WBS, RACI, Risks, Budget sheets."""
        wb = Workbook()
        if wb.active:
            wb.remove(wb.active)

        self._add_wbs_sheet(wb)
        self._add_raci_sheet(wb)
        self._add_risks_sheet(wb)
        self._add_budget_sheet(wb)

        path = self.output_dir / "project_artifacts.xlsx"
        wb.save(path)
        return path

    def _add_wbs_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("WBS")
        ws.append(["ID", "Name", "Duration (days)", "Dependencies"])
        ws[1][0].font = Font(bold=True)
        for task in self.blocks.get("wbs", {}).get("wbs", []):
            ws.append([
                task.get("id", ""),
                task.get("name", ""),
                task.get("duration_days", ""),
                str(task.get("dependencies", [])),
            ])

    def _add_raci_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("RACI")
        ws.append(["Role", "Responsible", "Accountable", "Consulted", "Informed"])
        ws[1][0].font = Font(bold=True)
        for row in self.blocks.get("raci", {}).get("raci_matrix", []):
            def _val(key: str) -> str:
                v = row.get(key, "")
                if isinstance(v, list):
                    return ", ".join(v)
                return str(v)
            ws.append([
                _val("role"),
                _val("responsible"),
                _val("accountable"),
                _val("consulted"),
                _val("informed"),
            ])

    def _add_risks_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("Risks")
        ws.append(["Description", "Probability", "Impact", "Mitigation", "Owner"])
        ws[1][0].font = Font(bold=True)
        for risk in self.blocks.get("risks", {}).get("risks", []):
            ws.append([
                risk.get("description", ""),
                risk.get("probability", ""),
                risk.get("impact", ""),
                risk.get("mitigation", ""),
                risk.get("owner", ""),
            ])

    def _add_budget_sheet(self, wb: Workbook) -> None:
        ws = wb.create_sheet("Budget")
        ws.append(["Item", "Estimated Cost", "Actual Cost"])
        ws[1][0].font = Font(bold=True)
        budget = self.blocks.get("budget", {}).get("budget", {})
        for item in budget.get("items", []):
            ws.append([
                item.get("name", ""),
                item.get("estimated_cost", 0),
                item.get("actual_cost", 0),
            ])
        ws.append(["", "Total:", budget.get("total", 0)])

    def generate_email(self) -> Path:
        """Create sponsor_email.txt with key project metrics."""
        wbs_tasks = self.blocks.get("wbs", {}).get("wbs", [])
        num_tasks = len(wbs_tasks)

        budget_data = self.blocks.get("budget", {}).get("budget", {})
        budget_total = budget_data.get("total", 0)

        risks = self.blocks.get("risks", {}).get("risks", [])
        main_risk = risks[0] if risks else {}
        risk_desc = main_risk.get("description", "N/A")
        risk_prob = main_risk.get("probability", "N/A")

        template = (
            f"Subject: Project Update — {self.project_name}\n\n"
            "Dear Sponsor,\n\n"
            f"Please find attached the project plan artifacts for "
            f'"{self.project_name}".\n\n'
            "Key Metrics:\n"
            f"- Total Budget: {budget_total}\n"
            f"- Number of WBS Tasks: {num_tasks}\n"
            f"- Top Risk: {risk_desc} (Probability: {risk_prob})\n\n"
            "The full project plan, WBS, RACI matrix, risk register, "
            "and budget breakdown are available in the attached Excel workbook.\n\n"
            "Best regards,\nProject Manager\n"
        )

        path = self.output_dir / "sponsor_email.txt"
        path.write_text(template, encoding="utf-8")
        return path
