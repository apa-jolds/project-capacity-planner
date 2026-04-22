# Project Capacity Planner

Project Capacity Planner is a Streamlit app for evaluating whether a portfolio of planned work fits within the available team capacity.

The current primary app is `app.py`. It models project-level capacity using project records plus resource allocations, then highlights overload, likely schedule slip, and estimated FTE gap.

## What The App Answers

- Is the current portfolio feasible as planned?
- Which resources are overloaded?
- How much weekly demand exceeds available capacity?
- Which projects are likely to slip?
- What additional FTE is needed to hold the planned dates?

## Current App Entry Point

- Primary app: `app.py`
- Alternate reconstruction reference: `app_reconstructed.py`

Unless explicitly directed otherwise, treat `app.py` as the active application.

## Data Files

The app reads local CSV files in the repo root:

- `projects.csv`: project metadata, dates, remaining hours, priority, and owner
- `allocations.csv`: resource-to-project allocation percentages
- `deliverables.csv`: legacy or reconstruction-supporting deliverable schedule data

## Main Features In `app.py`

- Executive dashboard with portfolio feasibility KPIs
- Resource capacity summary with weekly load status
- Project rollup summary with realistic end-date projections
- Staffing insight showing weekly overage and estimated FTE gap
- Editable Projects and Allocations tables using Streamlit data editors
- CSV-backed save flow for projects and allocations

## Capacity Assumptions

- Base capacity: `45` hours per week per resource
- Default contingency: `10%`
- Effective capacity formula: `45 * (1 - contingency)`
- Timelines expand when modeled demand exceeds effective capacity

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
- `app_reconstructed.py` is a separate reconstruction artifact and should not be overwritten without explicit instruction.
- Documentation and workflow expectations are tracked in `AGENTS.md` and `CURRENT_STATE.md`.
