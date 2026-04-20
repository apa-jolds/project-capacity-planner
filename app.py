from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="APEX | Apache Execution Planner", page_icon=":bar_chart:", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
PROJECTS_PATH = BASE_DIR / "projects.csv"
ALLOCATIONS_PATH = BASE_DIR / "allocations.csv"
DELIVERABLES_PATH = BASE_DIR / "deliverables.csv"

PROJECT_COLUMNS = ["project_id", "project_name", "start_date", "end_date", "remaining_hours", "priority", "owner"]
ALLOCATION_COLUMNS = ["allocation_id", "project_id", "resource_name", "allocation_pct"]
PRIORITY_OPTIONS = ["High", "Medium", "Low"]
WEEKLY_HOURS = 45.0
DAILY_HOURS = 9.0
DEFAULT_CONTINGENCY = 0.10

THEME = {
    "bg": "#eef2f6",
    "bg_top": "#f6f8fb",
    "card": "#ffffff",
    "text": "#0f172a",
    "muted": "#64748b",
    "border": "rgba(25,35,52,0.12)",
    "grid": "rgba(148,163,184,0.18)",
    "accent": "#d22630",
    "accent_soft": "rgba(210,38,48,0.12)",
    "healthy": "#16a34a",
    "amber": "#d97706",
    "risk": "#dc2626",
}


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, {THEME["bg_top"]}, transparent 34%),
                linear-gradient(180deg, {THEME["bg_top"]}, {THEME["bg"]});
        }}
        .hdr, .panel, .kpi {{
            background: {THEME["card"]};
            border: 1px solid {THEME["border"]};
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
        }}
        .hdr {{ padding: 1.35rem 1.5rem; margin-bottom: 1rem; }}
        .badge {{
            display: inline-block; padding: 0.28rem 0.58rem; border-radius: 999px;
            background: {THEME["accent_soft"]}; color: {THEME["accent"]}; font-size: 0.8rem; font-weight: 700;
        }}
        .kicker {{ color: {THEME["accent"]}; font-size: 2rem; font-weight: 800; margin-top: 0.45rem; }}
        .title {{ color: {THEME["text"]}; font-size: 1.9rem; font-weight: 700; }}
        .sub {{ color: {THEME["muted"]}; font-size: 1rem; margin-top: 0.25rem; }}
        .section {{ color: {THEME["text"]}; font-size: 1.04rem; font-weight: 700; margin: 0.35rem 0 0.55rem 0.1rem; }}
        .panel {{ padding: 1rem 1rem 0.85rem 1rem; margin-bottom: 1rem; }}
        .kpi {{ padding: 0.95rem 1rem; min-height: 118px; }}
        .kpi-l {{ color: {THEME["muted"]}; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
        .kpi-v {{ color: {THEME["text"]}; font-size: 1.8rem; font-weight: 800; margin-top: 0.4rem; }}
        .kpi-c {{ color: {THEME["muted"]}; font-size: 0.87rem; margin-top: 0.3rem; }}
        .banner {{
            background: {THEME["card"]}; border: 1px solid {THEME["border"]}; border-left: 4px solid {THEME["accent"]};
            border-radius: 18px; padding: 1rem 1.1rem; margin-bottom: 1rem;
        }}
        .banner-title {{ color: {THEME["text"]}; font-weight: 800; margin-bottom: 0.25rem; }}
        .banner-body {{ color: {THEME["muted"]}; line-height: 1.55; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_date_value(value: object) -> date | None:
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def format_date_for_csv(value: object) -> str:
    parsed = parse_date_value(value)
    return "" if parsed is None else parsed.isoformat()


def business_days(start_value: object, end_value: object) -> int:
    start_date = parse_date_value(start_value)
    end_date = parse_date_value(end_value)
    if start_date is None or end_date is None or end_date < start_date:
        return 0
    return len(pd.bdate_range(start=start_date, end=end_date))


def add_business_days(start_value: object, days: int) -> date | None:
    start_date = parse_date_value(start_value)
    if start_date is None:
        return None
    if days <= 0:
        return start_date
    return pd.bdate_range(start=start_date, periods=days)[-1].date()


def format_hours(value: float) -> str:
    return f"{value:,.1f} hrs"


def format_pct(value: float) -> str:
    return f"{value * 100:,.0f}%"


def capacity_status(load_pct: float) -> str:
    if load_pct > 1.0:
        return "Overallocated"
    if load_pct >= 0.85:
        return "Near capacity"
    return "Available"


def next_id(df: pd.DataFrame, column: str) -> int:
    series = pd.to_numeric(df.get(column), errors="coerce").dropna() if column in df.columns else pd.Series(dtype=float)
    return 1 if series.empty else int(series.max()) + 1


def normalize_projects(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=PROJECT_COLUMNS)
    out = df.copy()
    for col in PROJECT_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[PROJECT_COLUMNS]
    out["project_id"] = pd.to_numeric(out["project_id"], errors="coerce").fillna(0).astype(int)
    out["project_name"] = out["project_name"].apply(clean_text)
    out["start_date"] = pd.to_datetime(out["start_date"], errors="coerce")
    out["end_date"] = pd.to_datetime(out["end_date"], errors="coerce")
    out["remaining_hours"] = pd.to_numeric(out["remaining_hours"], errors="coerce").fillna(0.0).clip(lower=0.0)
    out["priority"] = out["priority"].apply(clean_text).replace("", "Medium")
    out["owner"] = out["owner"].apply(clean_text)
    return out.sort_values(["project_name", "project_id"]).reset_index(drop=True)


def normalize_allocations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)
    out = df.copy()
    for col in ALLOCATION_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[ALLOCATION_COLUMNS]
    out["allocation_id"] = pd.to_numeric(out["allocation_id"], errors="coerce").fillna(0).astype(int)
    out["project_id"] = pd.to_numeric(out["project_id"], errors="coerce").fillna(0).astype(int)
    out["resource_name"] = out["resource_name"].apply(clean_text)
    out["allocation_pct"] = pd.to_numeric(out["allocation_pct"], errors="coerce").fillna(0.0).clip(lower=0.0)
    return out.sort_values(["project_id", "resource_name", "allocation_id"]).reset_index(drop=True)


def migrate_projects() -> pd.DataFrame:
    raw = pd.read_csv(PROJECTS_PATH) if PROJECTS_PATH.exists() else pd.DataFrame()
    if set(PROJECT_COLUMNS).issubset(raw.columns):
        return normalize_projects(raw)
    deliverables = pd.read_csv(DELIVERABLES_PATH) if DELIVERABLES_PATH.exists() else pd.DataFrame()
    if deliverables.empty:
        base = raw.copy()
        if "project_id" not in base.columns:
            base["project_id"] = range(1, len(base) + 1)
        if "project_name" not in base.columns:
            base["project_name"] = base["project_id"].apply(lambda value: f"Project {value}")
        if "priority" not in base.columns:
            base["priority"] = "Medium"
        if "owner" not in base.columns:
            base["owner"] = ""
        base["start_date"] = pd.NaT
        base["end_date"] = pd.NaT
        base["remaining_hours"] = 0.0
        return normalize_projects(base)
    deliverables["project_id"] = pd.to_numeric(deliverables.get("project_id"), errors="coerce")
    deliverables["start_date"] = pd.to_datetime(deliverables.get("start_date"), errors="coerce")
    deliverables["end_date"] = pd.to_datetime(deliverables.get("end_date"), errors="coerce")
    deliverables["estimated_hours"] = deliverables.apply(lambda row: float(business_days(row["start_date"], row["end_date"])) * DAILY_HOURS, axis=1)
    rolled = deliverables.groupby("project_id", dropna=False).agg(
        start_date=("start_date", "min"),
        end_date=("end_date", "max"),
        remaining_hours=("estimated_hours", "sum"),
    ).reset_index()
    merged = raw.merge(rolled, on="project_id", how="left") if not raw.empty else rolled
    if "project_name" not in merged.columns:
        merged["project_name"] = merged["project_id"].apply(lambda value: f"Project {int(value)}")
    if "priority" not in merged.columns:
        merged["priority"] = "Medium"
    if "owner" not in merged.columns:
        merged["owner"] = ""
    return normalize_projects(merged)


def migrate_allocations() -> pd.DataFrame:
    raw = pd.read_csv(ALLOCATIONS_PATH) if ALLOCATIONS_PATH.exists() else pd.DataFrame()
    if set(ALLOCATION_COLUMNS).issubset(raw.columns):
        return normalize_allocations(raw)
    if raw.empty or "deliverable_id" not in raw.columns or not DELIVERABLES_PATH.exists():
        base = raw.copy()
        if "allocation_id" not in base.columns:
            base["allocation_id"] = range(1, len(base) + 1)
        if "project_id" not in base.columns:
            base["project_id"] = 0
        if "resource_name" not in base.columns:
            base["resource_name"] = ""
        if "allocation_pct" not in base.columns:
            base["allocation_pct"] = 0.0
        return normalize_allocations(base)
    deliverables = pd.read_csv(DELIVERABLES_PATH)
    deliverables["deliverable_id"] = pd.to_numeric(deliverables.get("deliverable_id"), errors="coerce")
    deliverables["project_id"] = pd.to_numeric(deliverables.get("project_id"), errors="coerce")
    merged = raw.merge(deliverables[["deliverable_id", "project_id"]], on="deliverable_id", how="left")
    rolled = merged.groupby(["project_id", "resource_name"], dropna=False).agg(allocation_pct=("allocation_pct", "sum")).reset_index()
    rolled["allocation_id"] = range(1, len(rolled) + 1)
    return normalize_allocations(rolled)


@st.cache_data(show_spinner=False)
def load_projects() -> pd.DataFrame:
    return migrate_projects()


@st.cache_data(show_spinner=False)
def load_allocations() -> pd.DataFrame:
    return migrate_allocations()


def save_projects(df: pd.DataFrame) -> None:
    out = normalize_projects(df).copy()
    out["start_date"] = out["start_date"].apply(format_date_for_csv)
    out["end_date"] = out["end_date"].apply(format_date_for_csv)
    out.to_csv(PROJECTS_PATH, index=False)


def save_allocations(df: pd.DataFrame) -> None:
    normalize_allocations(df).to_csv(ALLOCATIONS_PATH, index=False)


def validate_projects(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if df["project_name"].eq("").any():
        errors.append("Every project must have a project name.")
    invalid = df["start_date"].notna() & df["end_date"].notna() & (df["end_date"] < df["start_date"])
    if invalid.any():
        errors.append("Project end dates must be on or after start dates.")
    return errors


def validate_allocations(df: pd.DataFrame, projects_df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    valid_project_ids = set(projects_df["project_id"].tolist())
    if df["resource_name"].eq("").any():
        errors.append("Every allocation must include a resource name.")
    if not set(df["project_id"].tolist()).issubset(valid_project_ids):
        errors.append("Every allocation must reference an existing project.")
    return errors


def build_project_metrics(projects_df: pd.DataFrame, today_value: date) -> pd.DataFrame:
    metrics = projects_df.copy()
    metrics["planning_start"] = metrics["start_date"].apply(lambda value: max(parse_date_value(value) or today_value, today_value))
    metrics["remaining_business_days"] = metrics.apply(lambda row: business_days(row["planning_start"], row["end_date"]), axis=1)
    metrics["remaining_weeks"] = metrics["remaining_business_days"].apply(lambda value: value / 5 if value > 0 else 0.0)
    metrics["required_weekly_hours"] = metrics.apply(
        lambda row: float(row["remaining_hours"]) / row["remaining_weeks"] if row["remaining_weeks"] > 0 else (float(row["remaining_hours"]) if row["remaining_hours"] > 0 else 0.0),
        axis=1,
    )
    return metrics


def build_capacity_summary(project_metrics_df: pd.DataFrame, allocations_df: pd.DataFrame, contingency: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail = allocations_df.merge(
        project_metrics_df[["project_id", "project_name", "owner", "priority", "remaining_hours", "required_weekly_hours", "remaining_business_days", "end_date"]],
        on="project_id",
        how="left",
    ).copy()
    detail["allocation_pct"] = pd.to_numeric(detail["allocation_pct"], errors="coerce").fillna(0.0).clip(lower=0.0)
    detail["allocated_remaining_hours"] = detail["remaining_hours"].fillna(0.0) * detail["allocation_pct"]
    detail["required_weekly_hours"] = detail["required_weekly_hours"].fillna(0.0) * detail["allocation_pct"]
    effective_capacity = max(WEEKLY_HOURS * (1 - contingency), 0.0)
    if detail.empty:
        empty = pd.DataFrame(columns=["resource_name", "allocated_remaining_hours", "required_weekly_hours", "effective_weekly_capacity", "weekly_load_pct", "excess_weekly_hours", "overload_factor", "status", "project_list"])
        return empty, detail
    summary = detail.groupby("resource_name", dropna=False).agg(
        allocated_remaining_hours=("allocated_remaining_hours", "sum"),
        required_weekly_hours=("required_weekly_hours", "sum"),
        project_list=("project_name", lambda x: ", ".join(sorted({clean_text(item) for item in x if clean_text(item)}))),
    ).reset_index()
    summary["effective_weekly_capacity"] = effective_capacity
    summary["weekly_load_pct"] = summary.apply(lambda row: row["required_weekly_hours"] / row["effective_weekly_capacity"] if row["effective_weekly_capacity"] > 0 else 0.0, axis=1)
    summary["excess_weekly_hours"] = (summary["required_weekly_hours"] - summary["effective_weekly_capacity"]).clip(lower=0.0)
    summary["overload_factor"] = summary["weekly_load_pct"].clip(lower=1.0)
    summary["status"] = summary["weekly_load_pct"].apply(capacity_status)
    return summary.sort_values(["weekly_load_pct", "resource_name"], ascending=[False, True]).reset_index(drop=True), detail


def calculate_realistic_timeline(project_metrics_df: pd.DataFrame, allocation_detail_df: pd.DataFrame, capacity_summary_df: pd.DataFrame) -> pd.DataFrame:
    overload_lookup = capacity_summary_df.set_index("resource_name")["overload_factor"].to_dict() if not capacity_summary_df.empty else {}
    rows: list[dict[str, object]] = []
    for project in project_metrics_df.itertuples():
        project_allocs = allocation_detail_df[allocation_detail_df["project_id"] == project.project_id].copy()
        if project_allocs.empty:
            factor = 1.0
            constrained_resources: list[str] = []
        else:
            project_allocs["resource_overload_factor"] = project_allocs["resource_name"].map(lambda name: overload_lookup.get(name, 1.0)).fillna(1.0)
            constrained_resources = sorted(project_allocs.loc[project_allocs["resource_overload_factor"] > 1.0, "resource_name"].dropna().astype(str).unique().tolist())
            allocation_sum = project_allocs["allocation_pct"].sum()
            factor = max(float((project_allocs["allocation_pct"] * project_allocs["resource_overload_factor"]).sum() / allocation_sum), 1.0) if allocation_sum > 0 else 1.0
        realistic_days = max(int(round(project.remaining_business_days * factor)), int(project.remaining_business_days))
        realistic_end = add_business_days(project.planning_start, realistic_days) if realistic_days > 0 else parse_date_value(project.end_date)
        planned_end = parse_date_value(project.end_date)
        delay_days = max(business_days(planned_end, realistic_end) - 1, 0) if planned_end and realistic_end else 0
        rows.append(
            {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "owner": project.owner,
                "priority": project.priority,
                "start_date": parse_date_value(project.start_date),
                "planned_end_date": planned_end,
                "realistic_end_date": realistic_end,
                "remaining_hours": float(project.remaining_hours),
                "required_weekly_hours": float(project.required_weekly_hours),
                "delay_days": delay_days,
                "constrained_resources": ", ".join(constrained_resources) if constrained_resources else "None",
                "risk_status": "On plan" if delay_days == 0 else ("Moderate slip" if delay_days <= 10 else "High slip"),
            }
        )
    return pd.DataFrame(rows)


def build_staffing_insight(capacity_summary_df: pd.DataFrame, contingency: float) -> dict[str, object]:
    effective_capacity = max(WEEKLY_HOURS * (1 - contingency), 0.0)
    overloaded = capacity_summary_df[capacity_summary_df["required_weekly_hours"] > capacity_summary_df["effective_weekly_capacity"]].copy()
    overloaded["excess_weekly_hours"] = (overloaded["required_weekly_hours"] - overloaded["effective_weekly_capacity"]).clip(lower=0.0)
    excess = float(overloaded["excess_weekly_hours"].sum()) if not overloaded.empty else 0.0
    return {"overloaded_df": overloaded, "total_excess_weekly_hours": excess, "effective_weekly_capacity": effective_capacity, "fte_gap": (excess / effective_capacity if effective_capacity > 0 else 0.0)}


def render_kpi(label: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="kpi">
            <div class="kpi-l">{label}</div>
            <div class="kpi-v">{value}</div>
            <div class="kpi-c">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_css()
projects_df = load_projects()
allocations_df = load_allocations()
today = date.today()

with st.sidebar:
    st.markdown("### Planning Inputs")
    contingency = st.slider("Contingency", min_value=0, max_value=40, value=int(DEFAULT_CONTINGENCY * 100), step=1) / 100
    st.metric("Effective Capacity", format_hours(WEEKLY_HOURS * (1 - contingency)))

st.markdown(
    """
    <div class="hdr">
        <div class="badge">Apache | E&amp;P Applications</div>
        <div class="kicker">APEX</div>
        <div class="title">Apache Execution Planner</div>
        <div class="sub">Project Capacity Planner for E&amp;P Applications</div>
    </div>
    """,
    unsafe_allow_html=True,
)

dashboard_tab, projects_tab, allocations_tab = st.tabs(["Dashboard", "Projects", "Allocations"])

with projects_tab:
    st.markdown('<div class="section">Projects</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    project_editor_df = projects_df.copy() if not projects_df.empty else pd.DataFrame(columns=PROJECT_COLUMNS)
    edited_projects = st.data_editor(
        project_editor_df,
        key="projects_editor",
        width="stretch",
        height=460,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "project_id": st.column_config.NumberColumn("Project ID", disabled=True, width="small"),
            "project_name": st.column_config.TextColumn("Project", width="large"),
            "start_date": st.column_config.DateColumn("Start", format="YYYY-MM-DD", width="medium"),
            "end_date": st.column_config.DateColumn("End", format="YYYY-MM-DD", width="medium"),
            "remaining_hours": st.column_config.NumberColumn("Remaining Hours", min_value=0.0, step=8.0, format="%.1f", width="medium"),
            "priority": st.column_config.SelectboxColumn("Priority", options=PRIORITY_OPTIONS, width="small"),
            "owner": st.column_config.TextColumn("Owner", width="medium"),
        },
    )
    working_projects_df = normalize_projects(edited_projects)
    blank_project_ids = working_projects_df["project_id"] <= 0
    if blank_project_ids.any():
        new_id = next_id(projects_df, "project_id")
        for idx in working_projects_df[blank_project_ids].index:
            working_projects_df.at[idx, "project_id"] = new_id
            new_id += 1
    project_errors = validate_projects(working_projects_df)
    for error in project_errors:
        st.error(error)
    if st.button("Save Projects", type="primary", use_container_width=True, disabled=bool(project_errors)):
        save_projects(working_projects_df)
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

valid_project_ids = sorted(set(working_projects_df["project_id"].tolist()))

with allocations_tab:
    st.markdown('<div class="section">Allocations</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    allocation_editor_df = allocations_df.copy() if not allocations_df.empty else pd.DataFrame(columns=ALLOCATION_COLUMNS)
    edited_allocations = st.data_editor(
        allocation_editor_df,
        key="allocations_editor",
        width="stretch",
        height=460,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "allocation_id": st.column_config.NumberColumn("Allocation ID", disabled=True, width="small"),
            "project_id": st.column_config.SelectboxColumn("Project ID", options=valid_project_ids, width="small"),
            "resource_name": st.column_config.TextColumn("Resource", width="medium"),
            "allocation_pct": st.column_config.NumberColumn("Allocation %", min_value=0.0, step=0.05, format="%.2f", width="small"),
        },
    )
    working_allocations_df = normalize_allocations(edited_allocations)
    blank_allocation_ids = working_allocations_df["allocation_id"] <= 0
    if blank_allocation_ids.any():
        new_id = next_id(allocations_df, "allocation_id")
        for idx in working_allocations_df[blank_allocation_ids].index:
            working_allocations_df.at[idx, "allocation_id"] = new_id
            new_id += 1
    allocation_errors = validate_allocations(working_allocations_df, working_projects_df)
    for error in allocation_errors:
        st.error(error)
    if st.button("Save Allocations", type="primary", use_container_width=True, disabled=bool(allocation_errors)):
        save_allocations(working_allocations_df)
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

project_metrics_df = build_project_metrics(working_projects_df, today)
capacity_summary_df, allocation_detail_df = build_capacity_summary(project_metrics_df, working_allocations_df, contingency)
timeline_df = calculate_realistic_timeline(project_metrics_df, allocation_detail_df, capacity_summary_df)
staffing = build_staffing_insight(capacity_summary_df, contingency)

weekly_overage = float(staffing["total_excess_weekly_hours"])
fte_gap = float(staffing["fte_gap"])
overloaded_resources = int((capacity_summary_df["weekly_load_pct"] > 1.0).sum()) if not capacity_summary_df.empty else 0
slipping_projects = int((timeline_df["delay_days"] > 0).sum()) if not timeline_df.empty else 0
portfolio_feasible = overloaded_resources == 0 and slipping_projects == 0

with dashboard_tab:
    cols = st.columns(5, gap="medium")
    with cols[0]:
        render_kpi("Portfolio Feasible", "Yes" if portfolio_feasible else "No", "Current plan versus modeled capacity")
    with cols[1]:
        render_kpi("Overloaded Resources", str(overloaded_resources), "Resources above effective weekly capacity")
    with cols[2]:
        render_kpi("Weekly Overage", format_hours(weekly_overage), "Demand above available weekly capacity")
    with cols[3]:
        render_kpi("Estimated FTE Gap", f"{fte_gap:.2f}", "Additional capacity needed to hold dates")
    with cols[4]:
        render_kpi("Projects Likely to Slip", str(slipping_projects), "Projects expected to extend under current load")

    summary = "Current portfolio is feasible as planned." if portfolio_feasible else f"Current portfolio is constrained by {overloaded_resources} overloaded resource(s), {format_hours(weekly_overage)} of weekly overage, and {slipping_projects} project(s) likely to slip."
    st.markdown(f'<div class="banner"><div class="banner-title">Executive Portfolio Readout</div><div class="banner-body">{summary}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section">Resource Capacity Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    if capacity_summary_df.empty:
        st.info("Add allocations to calculate resource load and overload.")
    else:
        resource_display = capacity_summary_df.copy()
        resource_display["allocated_remaining_hours"] = resource_display["allocated_remaining_hours"].map(format_hours)
        resource_display["required_weekly_hours"] = resource_display["required_weekly_hours"].map(format_hours)
        resource_display["effective_weekly_capacity"] = resource_display["effective_weekly_capacity"].map(format_hours)
        resource_display["weekly_load_pct"] = resource_display["weekly_load_pct"].map(format_pct)
        st.dataframe(resource_display[["resource_name", "project_list", "allocated_remaining_hours", "required_weekly_hours", "effective_weekly_capacity", "weekly_load_pct", "status"]], width="stretch", height=320, hide_index=True)
        chart_df = capacity_summary_df.copy()
        chart_df["weekly_load_pct"] = chart_df["weekly_load_pct"] * 100
        fig = px.bar(chart_df, x="resource_name", y="weekly_load_pct", color="status", color_discrete_map={"Overallocated": THEME["risk"], "Near capacity": THEME["amber"], "Available": THEME["healthy"]})
        fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor=THEME["card"], plot_bgcolor=THEME["card"], font=dict(color=THEME["text"]))
        fig.update_xaxes(title=None, gridcolor=THEME["grid"])
        fig.update_yaxes(title=None, gridcolor=THEME["grid"])
        st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section">Project Rollup Summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    if timeline_df.empty:
        st.info("Add projects with dates, remaining hours, and allocations to evaluate slippage.")
    else:
        project_display = timeline_df.copy()
        for col in ["start_date", "planned_end_date", "realistic_end_date"]:
            project_display[col] = pd.to_datetime(project_display[col]).dt.strftime("%Y-%m-%d").fillna("")
        project_display["remaining_hours"] = project_display["remaining_hours"].map(format_hours)
        project_display["required_weekly_hours"] = project_display["required_weekly_hours"].map(format_hours)
        st.dataframe(project_display[["project_name", "owner", "priority", "start_date", "planned_end_date", "realistic_end_date", "remaining_hours", "required_weekly_hours", "delay_days", "constrained_resources", "risk_status"]], width="stretch", height=360, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section">Staffing Insight</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    if staffing["overloaded_df"].empty:
        st.markdown("Current staffing appears sufficient to support the modeled project dates.")
    else:
        st.markdown(f"**Excess weekly demand:** {format_hours(staffing['total_excess_weekly_hours'])}  \n**Approximate FTE gap:** {fte_gap:.2f} FTE  \n**Effective weekly capacity per resource:** {format_hours(staffing['effective_weekly_capacity'])}")
        overload_display = staffing["overloaded_df"].copy()
        overload_display["required_weekly_hours"] = overload_display["required_weekly_hours"].map(format_hours)
        overload_display["effective_weekly_capacity"] = overload_display["effective_weekly_capacity"].map(format_hours)
        overload_display["excess_weekly_hours"] = overload_display["excess_weekly_hours"].map(format_hours)
        overload_display["weekly_load_pct"] = overload_display["weekly_load_pct"].map(format_pct)
        st.dataframe(overload_display[["resource_name", "required_weekly_hours", "effective_weekly_capacity", "excess_weekly_hours", "weekly_load_pct"]], width="stretch", height=220, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
