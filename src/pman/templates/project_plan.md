# Project Plan: {{PROJECT_NAME}}

## Project Charter

### Business Case
<!-- Describe the business need and value proposition -->

### Project Objectives (SMART)
<!-- Specific, Measurable, Achievable, Relevant, Time-bound -->
- Objective 1:
- Objective 2:
- Objective 3:

### Scope

#### In-Scope
<!-- What is explicitly included in the project -->

#### Out-of-Scope
<!-- What is explicitly excluded from the project -->

### Constraints
<!-- Budget, time, resources, technical constraints -->

### Assumptions
<!-- List assumptions that, if invalidated, affect the plan -->

### Success Criteria
<!-- How do we know the project succeeded? -->

---

## Stakeholder Analysis & RACI Matrix

### Stakeholder Analysis
<!-- Identify key stakeholders, their interest, influence, and communication needs -->

### RACI Matrix

# BEGIN RACI
raci_matrix:
  - task: "Definire requisiti"
    responsible: "Product Owner"
    accountable: "Project Manager"
    consulted: ["Tech Lead"]
    informed: ["Stakeholder Board"]
  - task: "Sviluppo funzionalita"
    responsible: "Development Team"
    accountable: "Tech Lead"
    consulted: ["Product Owner"]
    informed: ["Stakeholder Board"]
# END RACI

---

## Work Breakdown Structure & Schedule

### WBS Overview
<!-- High-level description of the work breakdown -->

### Schedule
<!-- Timeline overview, milestones, critical path -->

# BEGIN WBS
wbs:
  - id: "1"
    name: "Project Initiation"
    sub:
      - id: "1.1"
        name: "Define scope"
        duration_days: 5
        dependencies: []
      - id: "1.2"
        name: "Assemble team"
        duration_days: 3
        dependencies: []
  - id: "2"
    name: "Planning"
    sub:
      - id: "2.1"
        name: "Create WBS"
        duration_days: 4
        dependencies: ["1.1"]
      - id: "2.2"
        name: "Estimate budget"
        duration_days: 3
        dependencies: ["1.1"]
# END WBS

---

## Risk Analysis

### Risk Overview
<!-- Qualitative analysis approach -->

### Risk Register

# BEGIN RISKS
risks:
  - description: "Ritardo nelle consegne"
    probability: "Medium"
    impact: "High"
    mitigation: "Buffer nel piano, stand-up giornalieri"
    owner: "Project Manager"
  - description: "Cambio requisiti"
    probability: "High"
    impact: "Medium"
    mitigation: "Freeze scope per sprint, change request formale"
    owner: "Product Owner"
# END RISKS

---

## Budget & Cost Estimation

### Budget Overview
<!-- Budget methodology (top-down, bottom-up, analogous) -->

### Cost Breakdown

# BEGIN BUDGET
budget:
  items:
    - category: "Risorse Umane"
      description: "Team sviluppo"
      estimated_cost: 50000
      notes: "3 mesi, 2 sviluppatori"
    - category: "Infrastruttura"
      description: "Server cloud, CI/CD"
      estimated_cost: 3000
      notes: "AWS / Azure"
  total: 53000
# END BUDGET
