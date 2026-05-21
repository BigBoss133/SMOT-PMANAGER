import tempfile
from pathlib import Path

from pman.bundle import BundleGenerator


SAMPLE_MARKDOWN = """
# BEGIN WBS
wbs:
  - id: "1.1"
    name: Design
    duration_days: 5
    dependencies: []
  - id: "1.2"
    name: Development
    duration_days: 10
    dependencies: ["1.1"]
# END WBS

# BEGIN RACI
raci_matrix:
  - role: PM
    responsible: Alice
    accountable: Bob
    consulted: Carol
    informed: Dave
# END RACI

# BEGIN RISKS
risks:
  - description: Budget overrun
    probability: high
    impact: high
    mitigation: Weekly review
    owner: Alice
# END RISKS

# BEGIN BUDGET
budget:
  items:
    - name: Design
      estimated_cost: 5000
      actual_cost: 0
    - name: Development
      estimated_cost: 10000
      actual_cost: 0
  total: 15000
# END BUDGET
"""


class TestBundleGenerator:
    def test_generate_excel(self):
        with tempfile.TemporaryDirectory() as tmp:
            gen = BundleGenerator("test-proj", SAMPLE_MARKDOWN, Path(tmp))
            path = gen.generate_excel()
            assert path.exists()
            assert path.name == "project_artifacts.xlsx"

    def test_generate_email(self):
        with tempfile.TemporaryDirectory() as tmp:
            gen = BundleGenerator("test-proj", SAMPLE_MARKDOWN, Path(tmp))
            path = gen.generate_email()
            assert path.exists()
            assert path.name == "sponsor_email.txt"
            text = path.read_text()
            assert "test-proj" in text
            assert "15000" in text
            assert "Budget overrun" in text
