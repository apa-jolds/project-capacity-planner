from __future__ import annotations

from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="APEX | Apache Execution Planner", page_icon=":bar_chart:", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
PROJECTS_PATH = BASE_DIR / "projects.csv"
DELIVERABLES_PATH = BASE_DIR / "deliverables.csv"
ALLOCATIONS_PATH = BASE_DIR / "allocations.csv"

PROJECT_COLUMNS = ["project_id", "project_name", "owner", "priority", "status", "notes"]
DELIVERABLE_COLUMNS = [
    "deliverable_id",
    "project_id",
    "deliverable_name",
    "start_date",
    "end_date",
    "status",
    "priority",
    "delivery_mode",
    "protected_delivery",
    "notes",
]
ALLOCATION_COLUMNS = ["allocation_id", "deliverable_id", "resource_name", "allocation_pct"]

WEEKLY_HOURS = 45.0
DAILY_HOURS = 9.0
DEFAULT_CONTINGENCY = 0.10
ACTIVE_DELIVERABLE_STATUSES = {"planned", "in progress", "at risk"}
LENS_OPTIONS = {"30 Days": 30, "60 Days": 60, "90 Days": 90, "180 Days": 180}

THEME = {
    "app_bg": "#0e1524",
    "app_bg_top": "#121b2d",
    "card_bg": "#1f2c44",
    "border": "rgba(148, 163, 184, 0.24)",
    "text": "#edf3fb",
    "text_muted": "#9fb0c9",
    "accent": "#d22630",
    "accent_soft": "rgba(210, 38, 48, 0.16)",
    "healthy": "#22c55e",
    "amber": "#f59e0b",
    "risk": "#ef4444",
    "grid": "rgba(148, 163, 184, 0.18)",
    "line_today": "rgba(210, 38, 48, 0.78)",
    "line_checkpoint": "rgba(245, 158, 11, 0.8)",
}


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_date_value(value: object) -> date | None:
    parsed = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def business_days(start_value: object, end_value: object) -> int:
    start_date = parse_date_value(start_value)
    end_date = parse_date_value(end_value)
    if start_date is None or end_date is None or end_date < start_date:
        return 0
    return len(pd.bdate_range(start=start_date, end=end_date))


def add_business_days(start_value: object, day_count: int) -> date | None:
    start_date = parse_date_value(start_value)
    if start_date is None:
        return None
    if day_count <= 0:
        return start_date
    return pd.bdate_range(start=start_date, periods=day_count)[-1].date()


def total_deliverable_hours(start_value: object, end_value: object, status: str) -> float:
    return 0.0 if clean_text(status).lower() in {"complete", "cancelled"} else float(business_days(start_value, end_value)) * DAILY_HOURS


def remaining_scope_hours(total_hours: float, status: str) -> float:
    return 0.0 if clean_text(status).lower() in {"complete", "cancelled"} else max(float(total_hours), 0.0)


def remaining_planned_business_days(start_value: object, end_value: object, today_value: date, status: str) -> int:
    if clean_text(status).lower() in {"complete", "cancelled"}:
        return 0
    start_date = parse_date_value(start_value)
    end_date = parse_date_value(end_value)
    if end_date is None:
        return 0
    planning_start = max(start_date or today_value, today_value)
    return business_days(planning_start, end_date)


def required_weekly_hours(remaining_hours: float, remaining_business_day_count: int) -> float:
    if remaining_hours <= 0:
        return 0.0
    remaining_weeks = remaining_business_day_count / 5 if remaining_business_day_count > 0 else 0.0
    return float(remaining_hours) / remaining_weeks if remaining_weeks > 0 else float(remaining_hours)


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


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, {THEME["app_bg_top"]}, transparent 34%),
                linear-gradient(180deg, {THEME["app_bg_top"]}, {THEME["app_bg"]});
        }}
        .app-header {{
            background: linear-gradient(135deg, rgba(210,38,48,0.14), rgba(31,44,68,0.96));
            border: 1px solid {THEME["border"]};
            border-radius: 22px;
            padding: 1.35rem 1.5rem;
            margin-bottom: 1rem;
        }}
        .brand-badge {{
            display: inline-block;
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            background: {THEME["accent_soft"]};
            color: #ffd3d7;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }}
        .app-kicker {{ color: #ffd8dc; font-size: 2rem; font-weight: 800; line-height: 1; }}
        .app-title {{ color: {THEME["text"]}; font-size: 1.9rem; font-weight: 700; margin-top: 0.15rem; }}
        .app-subtitle {{ color: {THEME["text_muted"]}; margin-top: 0.35rem; font-size: 1rem; }}
        .section-label {{ color: {THEME["text"]}; font-size: 1.04rem; font-weight: 700; margin: 0.45rem 0 0.55rem 0.1rem; }}
        .section-subtitle {{ color: {THEME["text_muted"]}; margin: -0.2rem 0 0.65rem 0.1rem; font-size: 0.92rem; }}
        .panel, .kpi-card {{
            background: {THEME["card_bg"]};
            border: 1px solid {THEME["border"]};
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(2, 6, 23, 0.22);
        }}
        .panel {{ padding: 1rem 1rem 0.85rem 1rem; margin-bottom: 1rem; }}
        .kpi-card {{ padding: 0.95rem 1rem; min-height: 120px; }}
        .kpi-label {{ color: {THEME["text_muted"]}; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
        .kpi-value {{ color: {THEME["text"]}; font-size: 1.8rem; font-weight: 800; margin-top: 0.4rem; line-height: 1.1; }}
        .kpi-caption {{ color: {THEME["text_muted"]}; font-size: 0.87rem; margin-top: 0.35rem; }}
        .banner {{
            background: {THEME["card_bg"]};
            border: 1px solid {THEME["border"]};
            border-left: 4px solid {THEME["accent"]};
            border-radius: 18px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }}
        .banner-title {{ color: {THEME["text"]}; font-weight: 800; margin-bottom: 0.25rem; }}
        .banner-body {{ color: {THEME["text_muted"]}; line-height: 1.55; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(label: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{escape(label)}</div>
            <div class="kpi-value">{escape(value)}</div>
            <div class="kpi-caption">{escape(caption)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def normalize_projects(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=PROJECT_COLUMNS)
    out = df.copy()
    for column in PROJECT_COLUMNS:
        if column not in out.columns:
            out[column] = ""
    out = out[PROJECT_COLUMNS]
    out["project_id"] = pd.to_numeric(out["project_id"], errors="coerce").astype("Int64")
    out["project_name"] = out["project_name"].apply(clean_text)
    out["owner"] = out["owner"].apply(clean_text)
    out["priority"] = out["priority"].apply(clean_text).replace("", "Medium")
    out["status"] = out["status"].apply(clean_text).replace("", "Planned")
    out["notes"] = out["notes"].apply(clean_text)
    return out.sort_values(["project_name", "project_id"]).reset_index(drop=True)


def normalize_deliverables(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=DELIVERABLE_COLUMNS)
    out = df.copy()
    for column in DELIVERABLE_COLUMNS:
        if column not in out.columns:
            out[column] = ""
    out = out[DELIVERABLE_COLUMNS]
    out["deliverable_id"] = pd.to_numeric(out["deliverable_id"], errors="coerce").astype("Int64")
    out["project_id"] = pd.to_numeric(out["project_id"], errors="coerce").astype("Int64")
    out["deliverable_name"] = out["deliverable_name"].apply(clean_text)
    out["start_date"] = pd.to_datetime(out["start_date"], errors="coerce")
    out["end_date"] = pd.to_datetime(out["end_date"], errors="coerce")
    out["status"] = out["status"].apply(clean_text).replace("", "Planned")
    out["priority"] = out["priority"].apply(clean_text).replace("", "Medium")
    out["delivery_mode"] = out["delivery_mode"].apply(clean_text).replace("", "Standard")
    out["protected_delivery"] = out["protected_delivery"].apply(clean_text).replace("", "No")
    out["notes"] = out["notes"].apply(clean_text)
    return out.sort_values(["project_id", "start_date", "deliverable_name", "deliverable_id"]).reset_index(drop=True)


def normalize_allocations(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=ALLOCATION_COLUMNS)
    out = df.copy()
    for column in ALLOCATION_COLUMNS:
        if column not in out.columns:
            out[column] = ""
    out = out[ALLOCATION_COLUMNS]
    out["allocation_id"] = pd.to_numeric(out["allocation_id"], errors="coerce").astype("Int64")
    out["deliverable_id"] = pd.to_numeric(out["deliverable_id"], errors="coerce").astype("Int64")
    out["resource_name"] = out["resource_name"].apply(clean_text)
    out["allocation_pct"] = pd.to_numeric(out["allocation_pct"], errors="coerce").fillna(0.0).clip(lower=0.0)
    return out.sort_values(["deliverable_id", "resource_name", "allocation_id"]).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_projects() -> pd.DataFrame:
    return normalize_projects(pd.read_csv(PROJECTS_PATH) if PROJECTS_PATH.exists() else pd.DataFrame(columns=PROJECT_COLUMNS))


@st.cache_data(show_spinner=False)
def load_deliverables() -> pd.DataFrame:
    return normalize_deliverables(pd.read_csv(DELIVERABLES_PATH) if DELIVERABLES_PATH.exists() else pd.DataFrame(columns=DELIVERABLE_COLUMNS))


@st.cache_data(show_spinner=False)
def load_allocations() -> pd.DataFrame:
    return normalize_allocations(pd.read_csv(ALLOCATIONS_PATH) if ALLOCATIONS_PATH.exists() else pd.DataFrame(columns=ALLOCATION_COLUMNS))


def build_deliverable_metrics(deliverables_df: pd.DataFrame, projects_df: pd.DataFrame, today_value: date) -> pd.DataFrame:
    metrics = deliverables_df.merge(projects_df, on="project_id", how="left", suffixes=("", "_project")).copy()
    metrics["total_deliverable_hours"] = metrics.apply(lambda row: total_deliverable_hours(row["start_date"], row["end_date"], str(row["status"])), axis=1)
    metrics["remaining_deliverable_hours"] = metrics.apply(
        lambda row: remaining_scope_hours(float(row["total_deliverable_hours"]), str(row["status"])),
        axis=1,
    )
    metrics["remaining_planned_business_days"] = metrics.apply(
        lambda row: remaining_planned_business_days(row["start_date"], row["end_date"], today_value, str(row["status"])),
        axis=1,
    )
    metrics["required_weekly_hours"] = metrics.apply(
        lambda row: required_weekly_hours(float(row["remaining_deliverable_hours"]), int(row["remaining_planned_business_days"])),
        axis=1,
    )
    metrics["timeline_label"] = metrics.apply(lambda row: f"{row['project_name']} | {row['deliverable_name']}", axis=1)
    metrics["is_active_status"] = metrics["status"].str.lower().isin(ACTIVE_DELIVERABLE_STATUSES)
    return metrics


def build_capacity_summary(deliverable_metrics_df: pd.DataFrame, allocations_df: pd.DataFrame, contingency_pct: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail = allocations_df.merge(
        deliverable_metrics_df[
            [
                "deliverable_id",
                "project_id",
                "project_name",
                "owner",
                "deliverable_name",
                "priority",
                "status",
                "delivery_mode",
                "protected_delivery",
                "start_date",
                "end_date",
                "remaining_deliverable_hours",
                "required_weekly_hours",
            ]
        ],
        on="deliverable_id",
        how="left",
    ).copy()
    detail["allocation_pct"] = detail["allocation_pct"].fillna(0.0).clip(lower=0.0)
    detail["allocated_remaining_hours"] = detail["remaining_deliverable_hours"].fillna(0.0) * detail["allocation_pct"]
    detail["required_weekly_hours"] = detail["required_weekly_hours"].fillna(0.0) * detail["allocation_pct"]
    effective_weekly_capacity = max(WEEKLY_HOURS * (1 - contingency_pct), 0.0)
    if detail.empty:
        return pd.DataFrame(columns=["resource_name", "active_deliverables", "allocated_remaining_hours", "required_weekly_hours", "effective_weekly_capacity", "weekly_load_pct", "excess_weekly_hours", "overload_factor", "status", "project_list"]), detail
    summary = (
        detail.groupby("resource_name", dropna=False)
        .agg(
            active_deliverables=("status", lambda s: int(pd.Series(s).fillna("").str.lower().isin(ACTIVE_DELIVERABLE_STATUSES).sum())),
            allocated_remaining_hours=("allocated_remaining_hours", "sum"),
            required_weekly_hours=("required_weekly_hours", "sum"),
            project_list=("project_name", lambda x: ", ".join(sorted({item for item in x if clean_text(item)}))),
        )
        .reset_index()
    )
    summary["effective_weekly_capacity"] = effective_weekly_capacity
    summary["weekly_load_pct"] = summary.apply(lambda row: row["required_weekly_hours"] / row["effective_weekly_capacity"] if row["effective_weekly_capacity"] > 0 else 0.0, axis=1)
    summary["excess_weekly_hours"] = (summary["required_weekly_hours"] - summary["effective_weekly_capacity"]).clip(lower=0.0)
    summary["overload_factor"] = summary["weekly_load_pct"].clip(lower=1.0)
    summary["status"] = summary["weekly_load_pct"].apply(capacity_status)
    return summary.sort_values(["weekly_load_pct", "resource_name"], ascending=[False, True]).reset_index(drop=True), detail


def calculate_realistic_timeline(deliverable_metrics_df: pd.DataFrame, allocation_detail_df: pd.DataFrame, capacity_summary_df: pd.DataFrame, today_value: date) -> pd.DataFrame:
    overload_lookup = capacity_summary_df.set_index("resource_name")["overload_factor"].to_dict() if not capacity_summary_df.empty else {}
    rows: list[dict[str, object]] = []
    for deliverable in deliverable_metrics_df.itertuples():
        planning_start = max(parse_date_value(deliverable.start_date) or today_value, today_value)
        planned_days = int(deliverable.remaining_planned_business_days)
        deliverable_allocs = allocation_detail_df[allocation_detail_df["deliverable_id"] == deliverable.deliverable_id].copy()
        if deliverable_allocs.empty:
            factor = 1.0
            constrained_resources: list[str] = []
        else:
            deliverable_allocs["resource_overload_factor"] = deliverable_allocs["resource_name"].map(lambda name: overload_lookup.get(name, 1.0)).fillna(1.0)
            constrained_resources = sorted(deliverable_allocs.loc[deliverable_allocs["resource_overload_factor"] > 1.0, "resource_name"].dropna().astype(str).unique().tolist())
            allocation_sum = deliverable_allocs["allocation_pct"].sum()
            factor = max(float((deliverable_allocs["allocation_pct"] * deliverable_allocs["resource_overload_factor"]).sum() / allocation_sum), 1.0) if allocation_sum > 0 else 1.0
        realistic_days = max(int(round(planned_days * factor)), planned_days, 0)
        realistic_end = add_business_days(planning_start, realistic_days) if realistic_days > 0 else parse_date_value(deliverable.end_date)
        planned_end = parse_date_value(deliverable.end_date)
        delay_days = max(business_days(planned_end, realistic_end) - 1, 0) if planned_end and realistic_end else 0
        rows.append(
            {
                "deliverable_id": deliverable.deliverable_id,
                "project_id": deliverable.project_id,
                "project_name": deliverable.project_name,
                "deliverable_name": deliverable.deliverable_name,
                "timeline_label": deliverable.timeline_label,
                "owner": deliverable.owner,
                "priority": deliverable.priority,
                "status": deliverable.status,
                "start_date": parse_date_value(deliverable.start_date),
                "planned_end_date": planned_end,
                "realistic_end_date": realistic_end,
                "remaining_deliverable_hours": float(deliverable.remaining_deliverable_hours),
                "required_weekly_hours": float(deliverable.required_weekly_hours),
                "delay_days": delay_days,
                "constrained_resources": ", ".join(constrained_resources) if constrained_resources else "None",
                "risk_status": "On plan" if delay_days == 0 else ("Moderate slip" if delay_days <= 10 else "High slip"),
            }
        )
    return pd.DataFrame(rows)


def build_project_rollups(projects_df: pd.DataFrame, deliverable_metrics_df: pd.DataFrame, realistic_timeline_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for project in projects_df.itertuples():
        deliverables = deliverable_metrics_df[deliverable_metrics_df["project_id"] == project.project_id].copy()
        timeline = realistic_timeline_df[realistic_timeline_df["project_id"] == project.project_id].copy()
        delay_days = int(timeline["delay_days"].max()) if not timeline.empty and (timeline["delay_days"] > 0).any() else 0
        constrained_resources = sorted(
            {
                item.strip()
                for value in timeline["constrained_resources"].fillna("")
                for item in str(value).split(",")
                if item.strip() and item.strip().lower() != "none"
            }
        )
        rows.append(
            {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "owner": project.owner,
                "priority": project.priority,
                "status": "At Risk" if delay_days > 0 else project.status,
                "deliverable_count": int(deliverables["deliverable_id"].notna().sum()),
                "active_deliverables": int(deliverables["is_active_status"].sum()) if not deliverables.empty else 0,
                "total_remaining_hours": float(deliverables["remaining_deliverable_hours"].sum()) if not deliverables.empty else 0.0,
                "required_weekly_hours": float(deliverables["required_weekly_hours"].sum()) if not deliverables.empty else 0.0,
                "planned_end_date": deliverables["end_date"].max() if not deliverables.empty else pd.NaT,
                "realistic_end_date": timeline["realistic_end_date"].max() if not timeline.empty else pd.NaT,
                "delay_days": delay_days,
                "constrained_resources": ", ".join(constrained_resources) if constrained_resources else "None",
                "risk_status": "On plan" if delay_days == 0 else ("Moderate slip" if delay_days <= 10 else "High slip"),
            }
        )
    return pd.DataFrame(rows)


def build_timeline_figure(timeline_df: pd.DataFrame, checkpoint_date: date) -> go.Figure:
    fig_df = timeline_df.dropna(subset=["start_date", "planned_end_date"]).copy()
    if fig_df.empty:
        return go.Figure()
    fig_df["task_label"] = fig_df["project_name"] + " | " + fig_df["deliverable_name"]
    fig = px.timeline(fig_df, x_start="start_date", x_end="planned_end_date", y="task_label", color="priority", color_discrete_map={"High": THEME["risk"], "Medium": THEME["amber"], "Low": THEME["healthy"]})
    fig.update_yaxes(autorange="reversed", title=None, tickfont=dict(size=11, color=THEME["text"]))
    fig.update_xaxes(title=None, showgrid=True, gridcolor=THEME["grid"], tickfont=dict(color=THEME["text_muted"]))
    fig.add_vline(x=pd.Timestamp(date.today()), line_width=2, line_dash="dash", line_color=THEME["line_today"])
    fig.add_vline(x=pd.Timestamp(checkpoint_date), line_width=2, line_dash="dot", line_color=THEME["line_checkpoint"])
    fig.update_layout(height=min(max(420, len(fig_df) * 36 + 160), 820), margin=dict(l=12, r=12, t=18, b=18), plot_bgcolor=THEME["card_bg"], paper_bgcolor=THEME["card_bg"], font=dict(color=THEME["text"]), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, font=dict(color=THEME["text_muted"])))
    return fig


def build_staffing_insight(capacity_summary_df: pd.DataFrame, contingency_pct: float) -> dict[str, object]:
    effective_capacity = max(WEEKLY_HOURS * (1 - contingency_pct), 0.0)
    overloaded = capacity_summary_df[capacity_summary_df["required_weekly_hours"] > capacity_summary_df["effective_weekly_capacity"]].copy()
    overloaded["excess_weekly_hours"] = (overloaded["required_weekly_hours"] - overloaded["effective_weekly_capacity"]).clip(lower=0.0)
    excess = float(overloaded["excess_weekly_hours"].sum()) if not overloaded.empty else 0.0
    return {"overloaded_df": overloaded, "total_excess_weekly_hours": excess, "effective_weekly_capacity_per_resource": effective_capacity, "fte_gap": (excess / effective_capacity if effective_capacity > 0 else 0.0)}


inject_css()
projects_df = load_projects()
deliverables_df = load_deliverables()
allocations_df = load_allocations()
today = date.today()

with st.sidebar:
    st.markdown("### Planning Controls")
    checkpoint_lens_label = st.selectbox("Checkpoint lens", list(LENS_OPTIONS.keys()), index=1)
    checkpoint_date = st.date_input("Checkpoint date", value=today + timedelta(days=LENS_OPTIONS[checkpoint_lens_label]))
    contingency_pct = st.slider("Daily hypercare / support contingency %", min_value=0, max_value=40, value=int(DEFAULT_CONTINGENCY * 100), step=1) / 100
    st.caption(f"Effective weekly capacity per resource: {format_hours(WEEKLY_HOURS * (1 - contingency_pct))}")
    project_filter = st.multiselect("Project", sorted(projects_df["project_name"].dropna().unique().tolist()))
    deliverable_filter = st.multiselect("Deliverable", sorted(deliverables_df["deliverable_name"].dropna().unique().tolist()))
    resource_filter = st.multiselect("Resource", sorted(allocations_df["resource_name"].dropna().unique().tolist()))
    owner_filter = st.multiselect("Owner", sorted(projects_df["owner"].dropna().unique().tolist()))
    priority_filter = st.multiselect("Priority", sorted({item for item in pd.concat([projects_df["priority"], deliverables_df["priority"]]).dropna().astype(str).tolist() if clean_text(item)}))
    status_filter = st.multiselect("Deliverable status", sorted(deliverables_df["status"].dropna().unique().tolist()))
    active_only = st.toggle("Show only active deliverables", value=False)

deliverable_metrics_df = build_deliverable_metrics(deliverables_df, projects_df, today)
capacity_summary_df, allocation_detail_df = build_capacity_summary(deliverable_metrics_df, allocations_df, contingency_pct)
realistic_timeline_df = calculate_realistic_timeline(deliverable_metrics_df, allocation_detail_df, capacity_summary_df, today)
project_rollups_df = build_project_rollups(projects_df, deliverable_metrics_df, realistic_timeline_df)
staffing = build_staffing_insight(capacity_summary_df, contingency_pct)

filtered_deliverables = deliverable_metrics_df.copy()
if project_filter:
    filtered_deliverables = filtered_deliverables[filtered_deliverables["project_name"].isin(project_filter)]
if deliverable_filter:
    filtered_deliverables = filtered_deliverables[filtered_deliverables["deliverable_name"].isin(deliverable_filter)]
if owner_filter:
    filtered_deliverables = filtered_deliverables[filtered_deliverables["owner"].isin(owner_filter)]
if priority_filter:
    filtered_deliverables = filtered_deliverables[filtered_deliverables["priority"].isin(priority_filter)]
if status_filter:
    filtered_deliverables = filtered_deliverables[filtered_deliverables["status"].isin(status_filter)]
if active_only:
    filtered_deliverables = filtered_deliverables[filtered_deliverables["is_active_status"]]
if resource_filter:
    scoped_ids = allocation_detail_df[allocation_detail_df["resource_name"].isin(resource_filter)]["deliverable_id"].dropna().unique().tolist()
    filtered_deliverables = filtered_deliverables[filtered_deliverables["deliverable_id"].isin(scoped_ids)]

filtered_capacity_summary = capacity_summary_df.copy()
if resource_filter:
    filtered_capacity_summary = filtered_capacity_summary[filtered_capacity_summary["resource_name"].isin(resource_filter)]
filtered_timeline = realistic_timeline_df[realistic_timeline_df["deliverable_id"].isin(filtered_deliverables["deliverable_id"].tolist())].copy()
filtered_projects_rollup = project_rollups_df[project_rollups_df["project_id"].isin(filtered_deliverables["project_id"].dropna().unique().tolist())].copy()
filtered_staffing = build_staffing_insight(filtered_capacity_summary, contingency_pct)

weekly_required_hours = float(filtered_deliverables["required_weekly_hours"].sum()) if not filtered_deliverables.empty else 0.0
weekly_effective_capacity = float(filtered_capacity_summary["effective_weekly_capacity"].sum()) if not filtered_capacity_summary.empty else max(WEEKLY_HOURS * (1 - contingency_pct), 0.0)
weekly_overage = float(filtered_capacity_summary["excess_weekly_hours"].sum()) if not filtered_capacity_summary.empty else 0.0
estimated_fte_gap = float(filtered_staffing["fte_gap"])
projects_likely_to_slip = int((filtered_projects_rollup["delay_days"] > 0).sum()) if not filtered_projects_rollup.empty else 0

st.markdown(
    """
    <div class="app-header">
        <div class="brand-badge">Apache | E&amp;P Applications</div>
        <div class="app-kicker">APEX</div>
        <div class="app-title">Apache Execution Planner</div>
        <div class="app-subtitle">Project Capacity Planner for E&amp;P Applications</div>
    </div>
    """,
    unsafe_allow_html=True,
)

kpi_cols = st.columns(6, gap="medium")
with kpi_cols[0]:
    render_kpi("Projects", str(int(filtered_projects_rollup["project_id"].nunique()) if not filtered_projects_rollup.empty else 0), "Initiatives in the current filtered plan")
with kpi_cols[1]:
    render_kpi("Deliverables", str(int(filtered_deliverables["deliverable_id"].nunique()) if not filtered_deliverables.empty else 0), "Schedulable work units in scope")
with kpi_cols[2]:
    render_kpi("Required Weekly Hours", format_hours(weekly_required_hours), "Weekly demand implied by planned deliverable dates")
with kpi_cols[3]:
    render_kpi("Effective Capacity", format_hours(weekly_effective_capacity), "Weekly capacity after hypercare/support contingency")
with kpi_cols[4]:
    render_kpi("Estimated FTE Gap", f"{estimated_fte_gap:.2f}", "Additional capacity needed to hold dates")
with kpi_cols[5]:
    render_kpi("Projects Likely to Slip", str(projects_likely_to_slip), "Projects expected to extend under current constraints")

summary_text = "Current portfolio is feasible as planned." if weekly_overage <= 0 and projects_likely_to_slip == 0 else f"Current portfolio is constrained by {int((filtered_capacity_summary['status'] == 'Overallocated').sum()) if not filtered_capacity_summary.empty else 0} overloaded resource(s), {format_hours(weekly_overage)} of weekly overage, and {projects_likely_to_slip} project(s) likely to slip."
st.markdown(f'<div class="banner"><div class="banner-title">Executive Portfolio Readout</div><div class="banner-body">{escape(summary_text)}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Planned Deliverable Timeline</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Reconstructed as a stable read-only timeline view from the surviving deliverable schedule data.</div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
if filtered_timeline.empty:
    st.info("No deliverables match the current filters.")
else:
    st.plotly_chart(build_timeline_figure(filtered_timeline, checkpoint_date), width="stretch")
    timeline_table = filtered_timeline.copy()
    timeline_table["start_date"] = pd.to_datetime(timeline_table["start_date"]).dt.strftime("%Y-%m-%d").fillna("")
    timeline_table["planned_end_date"] = pd.to_datetime(timeline_table["planned_end_date"]).dt.strftime("%Y-%m-%d").fillna("")
    timeline_table["realistic_end_date"] = pd.to_datetime(timeline_table["realistic_end_date"]).dt.strftime("%Y-%m-%d").fillna("")
    st.dataframe(timeline_table[["project_name", "deliverable_name", "owner", "priority", "status", "start_date", "planned_end_date", "realistic_end_date", "delay_days"]], width="stretch", height=260, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-label">Project Rollup Summary</div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
if filtered_projects_rollup.empty:
    st.info("No project rollups match the current filters.")
else:
    project_display = filtered_projects_rollup.copy()
    project_display["total_remaining_hours"] = project_display["total_remaining_hours"].map(format_hours)
    project_display["required_weekly_hours"] = project_display["required_weekly_hours"].map(format_hours)
    project_display["planned_end_date"] = pd.to_datetime(project_display["planned_end_date"]).dt.strftime("%Y-%m-%d").fillna("")
    project_display["realistic_end_date"] = pd.to_datetime(project_display["realistic_end_date"]).dt.strftime("%Y-%m-%d").fillna("")
    st.dataframe(project_display[["project_name", "owner", "priority", "status", "deliverable_count", "active_deliverables", "total_remaining_hours", "required_weekly_hours", "planned_end_date", "realistic_end_date", "delay_days", "constrained_resources", "risk_status"]], width="stretch", height=360, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="section-label">Resource Capacity Summary</div>', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
if filtered_capacity_summary.empty:
    st.info("No resource allocations match the current filters.")
else:
    capacity_display = filtered_capacity_summary.copy()
    capacity_display["allocated_remaining_hours"] = capacity_display["allocated_remaining_hours"].map(format_hours)
    capacity_display["required_weekly_hours"] = capacity_display["required_weekly_hours"].map(format_hours)
    capacity_display["effective_weekly_capacity"] = capacity_display["effective_weekly_capacity"].map(format_hours)
    capacity_display["weekly_load_pct"] = capacity_display["weekly_load_pct"].map(format_pct)
    st.dataframe(capacity_display[["resource_name", "active_deliverables", "allocated_remaining_hours", "required_weekly_hours", "effective_weekly_capacity", "weekly_load_pct", "status", "project_list"]], width="stretch", height=300, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

with st.expander("Reconstruction Notes", expanded=False):
    st.markdown(
        """
Faithfully reconstructed:
- Deliverables remain the schedulable units.
- Projects remain parent containers with project-level rollups.
- Capacity is based on 45 hrs/week less contingency.
- Required weekly hours, resource overload, slippage, and FTE gap are computed from the surviving CSVs.
- Planning Controls sidebar, KPI cards, executive readout, deliverable timeline section, and project rollup summary are all present.

Approximate because the original code is gone:
- The exact sidebar wording and control defaults beyond the surviving artifacts.
- The exact visual layout and column order from the lost UI screenshots.
- The interactive drag-and-drop timeline. This reconstruction intentionally uses a stable read-only Plotly timeline instead of a broken custom component.
- Any previous inline-edit or tab-specific management tooling beyond the sections explicitly requested.
        """
    )
