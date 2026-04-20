# Project Capacity Planner – Context

## Purpose
This application is a capacity planning and portfolio feasibility tool.

It answers:
- Can our team deliver projects by planned dates?
- If not:
  - Who is overloaded?
  - What work exceeds capacity?
  - Which projects slip?
  - How far do timelines extend?
  - What FTE is required?

---

## Core Concepts

### Projects
Define scope and timeline:
- project_id
- project_name
- start_date
- end_date
- priority
- owner
- progress_pct
- status

---

### Resource Allocations
Each row:
- allocation_id
- project_id
- resource_name
- allocation_pct

Rules:
- Many-to-many (resources ↔ projects)
- allocation_pct = % of capacity

---

### Capacity Model

Base:
- 9 hrs/day
- 5 days/week = 45 hrs/week

Contingency:
- Default 10%

Effective capacity:
45 * (1 - contingency) = 40.5 hrs/week

---

## Core Calculations

### Weekly Load %
required_weekly_hours / effective_weekly_capacity

### Checkpoint Utilization %
demand_hours_to_checkpoint / available_hours_to_checkpoint

### FTE Gap
weekly_overage / effective_weekly_capacity

---

## Key Principle

Work stays constant  
Capacity stays fixed  
Timeline expands  

---

## Dashboard Must Answer

1. Is the portfolio feasible?
2. Who is overloaded?
3. What slips?
4. Why?
5. What is the FTE gap?

---

## UX Principles

- Clean and executive-friendly
- Strong hierarchy
- No clutter
- Consistent dark theme
- Tooltips for clarity

---

## Allocations UX

- Editable table
- Inline edits
- Save to CSV
- Add/delete rows

---

## Core Insight

This tool shifts from:
"Are projects on track?"

To:
"Do we have enough capacity to deliver?"
