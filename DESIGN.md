# SMOT-PMANAGER Export & Delivery Dashboard

## Overview
A lightweight web dashboard that renders project bundle data exported by the CLI (`pman export <id> --json`). The dashboard reads a JSON payload and presents it as an interactive, printable report for stakeholders.

## Data Contract
The CLI prints a JSON object with this shape:
```json
{
  "project_name": "string",
  "wbs": [
    {"id": "1.1", "name": "Design", "duration_days": 5, "dependencies": []}
  ],
  "raci": [
    {"role": "PM", "responsible": "Alice", "accountable": "Bob", "consulted": "Carol", "informed": "Dave"}
  ],
  "risks": [
    {"description": "Budget overrun", "probability": "high", "impact": "high", "mitigation": "Weekly review", "owner": "Alice"}
  ],
  "budget": {
    "items": [{"name": "Design", "estimated_cost": 5000, "actual_cost": 0}],
    "total": 15000
  }
}
```

## UX Goals
- Single-page app, no backend required
- Load JSON via file input or paste
- Render 4 sections: WBS (Gantt-style table), RACI matrix, Risk heatmap, Budget chart
- Export to PDF via browser print
- Responsive, printable A4 layout

## Tech Stack
- React 18 + TypeScript
- Tailwind CSS for styling
- shadcn/ui components (Table, Card, Badge, Progress)
- Recharts for budget bar chart
- No build server: plain Vite output, static HTML deployable anywhere

## Component Breakdown
1. **AppShell**: header with project name, file loader, print button
2. **WBSTable**: sortable table with ID, Name, Duration, Dependencies
3. **RACIMatrix**: grid with Role/Responsible/Accountable/Consulted/Informed
4. **RiskBoard**: cards color-coded by probability × impact (low/medium/high)
5. **BudgetChart**: stacked bar chart (estimated vs actual) + total summary
6. **ExportToolbar**: "Print to PDF" and "Copy JSON" buttons

## Design Tokens
- Primary: `#0f172a` (slate-900)
- Accent: `#3b82f6` (blue-500)
- Risk low: `#22c55e`, medium: `#eab308`, high: `#ef4444`
- Font: Inter, system-ui
- Spacing: 1rem base, cards with shadow-sm

## File Structure
```
frontend/
  src/
    App.tsx
    components/
      WBSTable.tsx
      RACIMatrix.tsx
      RiskBoard.tsx
      BudgetChart.tsx
      ExportToolbar.tsx
    types/
      bundle.ts
  index.html
  vite.config.ts
```

## Acceptance Criteria
- [ ] Renders all 4 sections from JSON
- [ ] Risk cards use correct color coding
- [ ] Budget chart shows items + total
- [ ] Print stylesheet hides file loader, shows all sections
- [ ] Works in Chrome/Firefox/Safari without server
