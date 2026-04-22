# Project Capacity Planner - Context

## Purpose
This application is a capacity planning and portfolio feasibility tool.

It answers:
- Can our team deliver projects by planned dates?
- If not:
  - Who is overloaded?
  - What work exceeds capacity?
  - Which deliverables or projects slip?
  - How far do timelines extend?
  - What FTE is required?

---

## Core Concepts

### Projects
Define parent containers and ownership:
- project_id
- project_name
- owner
- priority
- status
- notes

---

### Deliverables
Define the schedulable work units used by the active app:
- deliverable_id
- project_id
- deliverable_name
- start_date
- end_date
- status
- priority
- delivery_mode
- protected_delivery
- notes

---

### Resource Allocations
Each row:
- allocation_id
- deliverable_id
- resource_name
- allocation_pct

Rules:
- Many-to-many (resources <-> deliverables)
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

### Deliverable Hours
business_days(start_date, end_date) * 9

### Weekly Load %
required_weekly_hours / effective_weekly_capacity

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
3. Which deliverables or projects slip?
4. Why?
5. What is the FTE gap?

---

## UX Principles

- Clean and executive-friendly
- Strong hierarchy
- No clutter
- Consistent dark theme
- Read-only analytical views over the current CSVs

---

## Current UI

- Filterable timeline view
- Project rollup summary
- Resource capacity summary
- Staffing insight

---

## Core Insight

This tool shifts from:
"Are projects on track?"

To:
"Do we have enough capacity to deliver?"
