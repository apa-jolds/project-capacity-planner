# Current State

## Active App

- Active application: `app.py`
- Source of active app: standardized deliverable-centric version
- Deprecated archive: `app_legacy.py`
- Framework: Streamlit
- Data source: local CSV files in the repo root

`app.py` is the primary app unless someone explicitly says otherwise. `app_legacy.py` is retained only as an archive of the previous implementation.

## What Currently Works

- The app launches as a Streamlit dashboard from `app.py`
- Projects, deliverables, and allocations are loaded directly from CSV files
- Portfolio feasibility KPIs are calculated from deliverable dates, allocations, and contingency
- Filterable deliverable timeline renders as a read-only Plotly view
- Project rollup summary estimates realistic end dates and likely slip from deliverable data
- Resource capacity summary identifies overloaded, near-capacity, and available resources
- Staffing insight estimates weekly overage and FTE gap
- Sidebar filters scope the dashboard by project, deliverable, resource, owner, priority, and status

## Current Data Shape

- `projects.csv` holds project metadata
- `deliverables.csv` holds the schedulable units
- `allocations.csv` maps resources to deliverables via `deliverable_id`
- The active app reads these files in their current deliverable-centric shape without migration

## Out Of Scope Right Now

- Restoring the deprecated project-level app as the default experience
- Deleting `app_legacy.py`
- Changing CSV schemas
- Introducing new planning features beyond the current standardized app
- Changing the current read-only timeline approach without explicit approval

## Current Priorities

1. Keep `app.py` stable as the primary application
2. Preserve the current deliverable-centric behavior and read-only timeline
3. Make the repo state understandable for future edits
4. Avoid accidental changes to `app_legacy.py` unless a task explicitly requires it
5. Keep documentation aligned with the standardized app structure

## Working Assumption For Future Changes

Unless a task explicitly says otherwise:

- make changes against `app.py`
- treat `app_legacy.py` as a deprecated archive
- preserve existing working behavior before attempting feature changes or refactors
