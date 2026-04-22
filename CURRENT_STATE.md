# Current State

## Active App

- Active application: `app.py`
- Framework: Streamlit
- Data source: local CSV files in the repo root

`app.py` is the primary app unless someone explicitly says otherwise.

## What Currently Works

- The app launches as a Streamlit dashboard from `app.py`
- Projects and allocations are loaded from CSV files
- Legacy data can be normalized into the project/allocation model used by `app.py`
- Portfolio feasibility KPIs are calculated from remaining hours, dates, allocations, and contingency
- Resource capacity summary identifies overloaded, near-capacity, and available resources
- Project rollup summary estimates realistic end dates and likely slip
- Staffing insight estimates weekly overage and FTE gap
- Projects table supports inline editing and saving back to `projects.csv`
- Allocations table supports inline editing and saving back to `allocations.csv`

## Current Data Shape

- `projects.csv` is already aligned with the active app's project-level model
- `allocations.csv` is already aligned with the active app's project allocation model
- `deliverables.csv` still exists and is used as migration support when older project data structures are encountered

## Out Of Scope Right Now

- Replacing `app.py` with `app_reconstructed.py`
- Overwriting or deleting reconstruction artifacts without explicit approval
- Removing working dashboard sections or save flows without approval
- Major app-logic changes before documentation and current-state cleanup are finished
- Reintroducing old custom timeline behavior from the reconstructed app

## Current Priorities

1. Keep `app.py` stable as the primary application
2. Preserve working functionality while documentation and workflow rules are clarified
3. Make the repo state understandable for future edits
4. Avoid accidental changes to `app_reconstructed.py` unless a task explicitly requires it
5. Use documentation to clarify what is active, what is legacy, and what should be handled carefully

## Working Assumption For Future Changes

Unless a task explicitly says otherwise:

- make changes against `app.py`
- treat `app_reconstructed.py` as a protected reference file
- preserve existing working behavior before attempting feature changes or refactors
