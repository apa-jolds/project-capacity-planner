# Project Capacity Planner

Project Capacity Planner is a Streamlit app for evaluating whether a portfolio of planned work fits within the available team capacity.

The current primary app is `app.py`. It is the standardized deliverable-centric application and models capacity from projects, deliverables, and resource allocations, then highlights overload, likely schedule slip, and estimated FTE gap.

## What The App Answers

- Is the current portfolio feasible as planned?
- Which resources are overloaded?
- How much weekly demand exceeds available capacity?
- Which projects are likely to slip?
- What additional FTE is needed to hold the planned dates?

## Current App Entry Point

- Primary app: `app.py`
- Archived legacy app: `app_legacy.py`

Unless explicitly directed otherwise, treat `app.py` as the active application and `app_legacy.py` as a deprecated reference.

## Data Files

The app reads local CSV files in the repo root:

- `projects.csv`: project metadata such as owner, priority, status, and notes
- `deliverables.csv`: deliverable schedule data with start/end dates and status
- `allocations.csv`: resource-to-deliverable allocation percentages

## Main Features In `app.py`

- Executive dashboard with portfolio feasibility KPIs
- Filterable deliverable timeline view
- Project rollup summary with realistic end-date projections
- Resource capacity summary with weekly load status
- Staffing insight showing weekly overage and estimated FTE gap
- Editable Projects, Deliverables, and Allocations management tabs with CSV save actions

## Capacity Assumptions

- Base capacity: `45` hours per week per resource
- Default contingency: `10%`
- Effective capacity formula: `45 * (1 - contingency)`
- Deliverable timelines expand when modeled demand exceeds effective capacity

## Run Locally

1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Start the app:

```powershell
streamlit run app.py
```

## Repository Notes

- `app.py` is the working app to preserve unless a task explicitly says otherwise.
- `app_legacy.py` preserves the previous project-level implementation and should only be modified if a task explicitly targets it.
- Documentation and workflow expectations are tracked in `AGENTS.md` and `CURRENT_STATE.md`.
