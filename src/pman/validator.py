from dataclasses import dataclass, field

import yaml


@dataclass
class CompletenessReport:
    overall_score: int = 0
    missing_sections: list[str] = field(default_factory=list)
    yaml_errors: list[str] = field(default_factory=list)
    text_warnings: list[str] = field(default_factory=list)


_YAML_BLOCK_RE = [
    ("raci", "# BEGIN RACI", "# END RACI"),
    ("wbs", "# BEGIN WBS", "# END WBS"),
    ("risks", "# BEGIN RISKS", "# END RISKS"),
    ("budget", "# BEGIN BUDGET", "# END BUDGET"),
]

_SECTION_HEADINGS = [
    ("Project Charter", "## Project Charter"),
    ("Stakeholder Analysis & RACI Matrix", "## Stakeholder Analysis & RACI Matrix"),
    ("Work Breakdown Structure & Schedule", "## Work Breakdown Structure & Schedule"),
    ("Risk Analysis", "## Risk Analysis"),
    ("Budget & Cost Estimation", "## Budget & Cost Estimation"),
]


class ProjectValidator:
    def get_sections(self) -> list[str]:
        return [name for name, _ in _SECTION_HEADINGS]

    def parse_sections(self, content: str) -> dict[str, str]:
        sections: dict[str, str] = {}
        for name, heading in _SECTION_HEADINGS:
            start = content.find(heading)
            if start == -1:
                sections[name] = ""
                continue
            end = len(content)
            for _, next_heading in _SECTION_HEADINGS:
                next_pos = content.find(next_heading, start + len(heading))
                if next_pos != -1 and next_pos < end:
                    end = next_pos
            sections[name] = content[start:end].strip()
        return sections

    def parse_yaml_blocks(self, content: str) -> dict[str, dict]:
        blocks: dict[str, dict] = {}
        for block_name, start_marker, end_marker in _YAML_BLOCK_RE:
            start = content.find(start_marker)
            end = content.find(end_marker, start)
            if start == -1 or end == -1:
                blocks[block_name] = {}
                continue
            yaml_text = content[start + len(start_marker):end].strip()
            try:
                blocks[block_name] = yaml.safe_load(yaml_text) or {}
            except yaml.YAMLError:
                blocks[block_name] = {}
        return blocks

    def validate_raci(self, raci_data: dict) -> list[str]:
        errors = []
        matrix = raci_data.get("raci_matrix", [])
        if not matrix:
            return ["RACI matrix is empty"]
        for idx, row in enumerate(matrix):
            accountable = row.get("accountable", "")
            if not accountable:
                errors.append(f"RACI row {idx}: missing Accountable")
            responsible = row.get("responsible", "")
            if not responsible:
                errors.append(f"RACI row {idx}: missing Responsible")
        return errors

    def validate_budget(self, budget_data: dict) -> list[str]:
        errors = []
        items = budget_data.get("budget", {}).get("items", [])
        total = budget_data.get("budget", {}).get("total", 0)
        if not items:
            return ["Budget items are empty"]
        calculated = sum(item.get("estimated_cost", 0) for item in items)
        if calculated != total:
            errors.append(f"Budget total mismatch: {calculated} != {total}")
        return errors

    def validate_wbs(self, wbs_data: dict) -> list[str]:
        errors = []
        wbs = wbs_data.get("wbs", [])
        if not wbs:
            return ["WBS is empty"]
        ids = set()
        for task in wbs:
            tid = task.get("id", "")
            if tid in ids:
                errors.append(f"WBS duplicate ID: {tid}")
            ids.add(tid)
        return errors

    def check_completeness(self, content: str) -> CompletenessReport:
        report = CompletenessReport()
        sections = self.parse_sections(content)
        blocks = self.parse_yaml_blocks(content)

        for name, text in sections.items():
            word_count = len(text.split())
            if word_count < 20:
                report.missing_sections.append(name)
                report.text_warnings.append(f"{name}: only {word_count} words (min 20)")
            elif word_count < 50:
                report.text_warnings.append(f"{name}: only {word_count} words (recommended 50+)")

        if "raci" in blocks:
            report.yaml_errors.extend(self.validate_raci(blocks["raci"]))
        if "budget" in blocks:
            report.yaml_errors.extend(self.validate_budget(blocks["budget"]))
        if "wbs" in blocks:
            report.yaml_errors.extend(self.validate_wbs(blocks["wbs"]))

        filled = len(sections) - len(report.missing_sections)
        report.overall_score = int((filled / len(sections)) * 100)
        return report
