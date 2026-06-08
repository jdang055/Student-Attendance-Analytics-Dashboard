"""
dashboard.py
------------
The main Streamlit app. Run it with:
    streamlit run dashboard.py

It loads the demo dataset by default. Users can upload their own CSV
using the sidebar file uploader.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from data_processor import process_attendance_file, CHRONIC_ABSENTEEISM_THRESHOLD
from report_exporter import generate_html_report

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Attendance Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── Styling ───────────────────────────────────────────────────────────────────
# Visual theme mirrors the Tableau Beginner Dashboard reference:
#   - Light gray page background (#f2f2f2)
#   - White chart panels with a subtle dashed border
#   - Colored pastel KPI cards (blue / orange / green / tan)
#   - Bold dark section headers
st.markdown("""
<style>
  /* ── Page background ── */
  .stApp                { background-color: #f2f2f2; }
  .block-container      { padding-top: 1.2rem; padding-bottom: 2rem; background-color: #f2f2f2; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] { background-color: #e8e8e8; }

  /* ── Chart panels: white card with Tableau-style dashed border ── */
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: white;
    border: 1px dashed #c0c0c0 !important;
    border-radius: 4px;
    padding: 12px 16px 4px 16px;
  }

  /* ── Section header style (bold, dark, like Tableau section labels) ── */
  h3 {
    font-family: 'Segoe UI', Arial, sans-serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #1a1a1a !important;
    margin-bottom: 4px !important;
  }

  /* ── Page title (h1) and all body text → dark black ── */
  h1, h2 {
    color: #1a1a1a !important;
  }

  /* ── Caption / subtext (data label line under title) ── */
  [data-testid="stCaptionContainer"] p,
  .stCaption, small {
    color: #1a1a1a !important;
    font-weight: 500 !important;
  }

  /* ── All generic paragraph and label text on the page ── */
  p, label, span, div {
    color: #1a1a1a;
  }

  /* ── Sidebar text ── */
  [data-testid="stSidebar"] p,
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] span,
  [data-testid="stSidebar"] .stCaption {
    color: #1a1a1a !important;
  }

  /* ── File uploader box → white background, black text ── */
  [data-testid="stFileUploader"] {
    background-color: white !important;
    border-radius: 6px;
  }
  [data-testid="stFileUploader"] * {
    color: #1a1a1a !important;
  }
  [data-testid="stFileUploaderDropzone"] {
    background-color: white !important;
    border: 1px dashed #aaa !important;
  }
  /* Browse files button inside the uploader */
  [data-testid="stFileUploaderDropzone"] button,
  [data-testid="stFileUploader"] button {
    background-color: white !important;
    color: #1a1a1a !important;
    border: 1px solid #aaa !important;
  }

  /* ── Download button → white background, black text ── */
  [data-testid="stDownloadButton"] button {
    background-color: white !important;
    color: #1a1a1a !important;
    border: 1px solid #aaa !important;
  }
  [data-testid="stDownloadButton"] button:hover {
    background-color: #f0f0f0 !important;
    border-color: #888 !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/1a237e/ffffff?text=Attendance+Hub",
             use_container_width=True)
    st.markdown("---")
    st.subheader("Data Source")

    uploaded_file = st.file_uploader(
        "Upload your own attendance CSV",
        type=["csv"],
        help="Must include: student_id, student_name, site_name, program_name, date, present",
    )

    st.markdown("---")
    st.caption(
        "**Column requirements**\n"
        "- `student_id` — unique student ID\n"
        "- `student_name` — full name\n"
        "- `site_name` — program location\n"
        "- `program_name` — program type\n"
        "- `date` — any standard date format\n"
        "- `present` — 1/0, True/False, or Present/Absent"
    )


# ── Load Data ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading and processing data...")
def load_data(source) -> tuple[pd.DataFrame, dict]:
    """
    Cache processed results so re-renders don't re-process the whole file.
    Streamlit re-runs this whenever 'source' changes.
    """
    return process_attendance_file(source)


# Decide whether to use the uploaded file or the bundled demo CSV
demo_path = Path(__file__).parent / "demo_attendance.csv"

if uploaded_file is not None:
    data_source = uploaded_file
    data_label  = f"Uploaded file: **{uploaded_file.name}**"
elif demo_path.exists():
    data_source = str(demo_path)
    data_label  = "Using **demo dataset** — upload your own CSV in the sidebar to replace it."
else:
    st.error(
        "No data found. Please run `python generate_data.py` first to create the demo dataset, "
        "or upload your own CSV using the sidebar."
    )
    st.stop()

# Attempt to load; show a friendly error if the file is malformed
try:
    clean_df, metrics = load_data(data_source)
except ValueError as error:
    st.error(f"**Could not read the file:** {error}")
    st.stop()


# ── Page Header ───────────────────────────────────────────────────────────────
# Rendered as HTML to guarantee black text regardless of Streamlit's active
# color theme (dark/light mode can override st.title and st.caption colors).
st.markdown(f"""
<div style="margin-top: 16px; margin-bottom: 12px;">
  <div style="font-family:'Segoe UI',Arial,sans-serif; font-size:2rem;
              font-weight:700; color:#1a1a1a; line-height:1.4; padding-top:4px;">
    Student Attendance Analytics
  </div>
  <div style="font-family:'Segoe UI',Arial,sans-serif; font-size:0.88rem;
              color:#1a1a1a; margin-top:4px; font-weight:500;">
    {data_label.replace("**", "")}
  </div>
</div>
<hr style="border:none; border-top:1px solid #cccccc; margin-bottom:16px;">
""", unsafe_allow_html=True)


# ── Section 1: KPI Summary Cards ──────────────────────────────────────────────
# Rendered as custom HTML so each card can have a Tableau-style colored
# background (pastel blue / orange / green / tan), matching the reference.

overall_pct     = metrics["overall_rate"] * 100
benchmark_delta = overall_pct - 90.0
chronic_pct     = metrics["chronic_rate"] * 100

# Delta label color: green if at/above 90%, red if below
delta_color     = "#2e7a34" if benchmark_delta >= 0 else "#c0392b"
delta_sign      = "▲" if benchmark_delta >= 0 else "▼"

# Support count color: gray when zero, red when students need help
support_color   = "#c0392b" if metrics["chronic_count"] > 0 else "#2e7a34"

CARD_STYLE = (
    "flex:1; border-radius:4px; padding:18px 16px; text-align:center; "
    "font-family:'Segoe UI',Arial,sans-serif;"
)
LABEL_STYLE = "font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#444; margin-bottom:6px;"
VALUE_STYLE = "font-size:2rem; font-weight:700; color:#1a1a1a; line-height:1.1;"
SUB_STYLE   = "font-size:0.78rem; margin-top:5px; color:#555;"

st.markdown(f"""
<div style="display:flex; gap:12px; margin-bottom:18px;">

  <div style="{CARD_STYLE} background:#aecde8;">
    <div style="{LABEL_STYLE}">Overall Attendance Rate</div>
    <div style="{VALUE_STYLE}">{overall_pct:.1f}%</div>
    <div style="{SUB_STYLE}; color:{delta_color}; font-weight:600;">
      {delta_sign} {abs(benchmark_delta):.1f}% vs. 90% goal
    </div>
  </div>

  <div style="{CARD_STYLE} background:#f7c9a3;">
    <div style="{LABEL_STYLE}">Students Enrolled</div>
    <div style="{VALUE_STYLE}">{metrics['total_students']:,}</div>
    <div style="{SUB_STYLE}">across all sites</div>
  </div>

  <div style="{CARD_STYLE} background:#c6deb8;">
    <div style="{LABEL_STYLE}">Attendance Records</div>
    <div style="{VALUE_STYLE}">{metrics['total_sessions']:,}</div>
    <div style="{SUB_STYLE}">total sessions tracked</div>
  </div>

  <div style="{CARD_STYLE} background:#ead8b4;">
    <div style="{LABEL_STYLE}">Students Needing Support</div>
    <div style="{VALUE_STYLE}; color:{support_color};">{metrics['chronic_count']}</div>
    <div style="{SUB_STYLE}">{chronic_pct:.1f}% of enrolled students</div>
  </div>

</div>
""", unsafe_allow_html=True)


# ── Shared Tableau-style theme ────────────────────────────────────────────────
# Applied consistently to all three charts so they feel like one cohesive report.
# Key decisions mirroring Tableau defaults:
#   - White plot background, no border or box
#   - Light gray horizontal gridlines only (no vertical noise on bar charts)
#   - Axis tick labels in medium gray; no axis line drawn
#   - Value labels in dark charcoal, positioned outside bars
#   - Muted, professional color palette (not neon/saturated)
#   - Keynote annotation top-right; dashed reference line with no floating text

TABLEAU_FONT   = "Segoe UI, Arial, sans-serif"
TABLEAU_GRAY   = "#5a5a5a"    # axis labels, tick text
TABLEAU_GRID   = "#e8e8e8"    # gridline color — barely-there, like Tableau
TABLEAU_BG     = "white"
LABEL_COLOR    = "#1a1a1a"    # near-black for value labels on bars
KEYNOTE_COLOR  = "#333333"    # dark charcoal for the 90% keynote — clearly readable
REF_LINE_COLOR = "#b0b0b0"    # light gray dashed reference line

def tableau_base_layout(height: int, margin: dict) -> dict:
    """Return a layout dict with Tableau-style chrome applied."""
    return dict(
        plot_bgcolor=TABLEAU_BG,
        paper_bgcolor=TABLEAU_BG,
        font=dict(family=TABLEAU_FONT, color=TABLEAU_GRAY),
        height=height,
        margin=margin,
        # Remove the default box border around the plot area
        xaxis=dict(
            showline=False,
            showgrid=False,
            tickfont=dict(color=TABLEAU_GRAY, size=11),
            title_font=dict(color=TABLEAU_GRAY, size=11),
            zeroline=False,
        ),
        yaxis=dict(
            showline=False,
            gridcolor=TABLEAU_GRID,
            gridwidth=1,
            tickfont=dict(color=TABLEAU_GRAY, size=11),
            title_font=dict(color=TABLEAU_GRAY, size=11),
            zeroline=False,
        ),
    )


# ── Tableau palette (shared across all charts) ────────────────────────────────
TABLEAU_PALETTE = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
                   "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac"]

# ── Section 2: Attendance by Site ─────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Attendance by Site")

    site_df = metrics["rate_by_site"].copy()
    site_df["attendance_pct"] = site_df["attendance_rate"] * 100
    site_df["status"] = site_df["attendance_rate"].apply(
        lambda r: "On Track (≥90%)" if r >= CHRONIC_ABSENTEEISM_THRESHOLD else "Needs Attention (<90%)"
    )

    site_x_min = max(70, site_df["attendance_pct"].min() - 5)
    site_x_max = min(100, site_df["attendance_pct"].max() + 4)

    bar_chart = px.bar(
        site_df,
        x="attendance_pct",
        y="site_name",
        orientation="h",
        color="status",
        color_discrete_map={
            "On Track (≥90%)":        "#4e79a7",
            "Needs Attention (<90%)": "#e15759",
        },
        text=site_df["attendance_pct"].map(lambda v: f"{v:.1f}%"),
        labels={"attendance_pct": "Attendance Rate (%)", "site_name": "", "status": ""},
    )

    layout = tableau_base_layout(height=320, margin=dict(l=10, r=20, t=55, b=10))
    layout["xaxis"]["showgrid"]  = True
    layout["xaxis"]["gridcolor"] = TABLEAU_GRID
    layout["yaxis"]["showgrid"]  = False
    layout["xaxis"]["range"]     = [site_x_min, site_x_max]
    layout["xaxis"]["title"]     = "Attendance Rate (%)"
    layout["yaxis"]["title"]     = ""
    layout["showlegend"] = True
    layout["legend"] = dict(
        orientation="h", x=0, y=1.12,
        font=dict(size=11, color=TABLEAU_GRAY),
        bgcolor="rgba(0,0,0,0)", borderwidth=0,
    )

    bar_chart.update_layout(**layout)
    bar_chart.update_traces(
        textposition="outside",
        textfont=dict(color=LABEL_COLOR, size=11, family=TABLEAU_FONT),
        marker_line_width=0,
    )
    bar_chart.add_vline(x=90, line_dash="dot", line_color=REF_LINE_COLOR, line_width=1.5)
    bar_chart.add_annotation(
        text="<b>· · ·  90% Attendance Goal</b>",
        xref="paper", yref="paper",
        x=1.0, y=1.18,
        xanchor="right", yanchor="bottom",
        showarrow=False,
        font=dict(size=11, color=KEYNOTE_COLOR, family=TABLEAU_FONT),
    )

    st.plotly_chart(bar_chart, use_container_width=True)


# ── Section 3: Weekly Attendance Trend ────────────────────────────────────────
with st.container(border=True):
    st.subheader("Weekly Attendance Trend")

    trend_df = metrics["weekly_trend"].copy()
    trend_df["attendance_pct"] = trend_df["attendance_rate"] * 100

    trend_y_min = max(70, trend_df["attendance_pct"].min() - 3)
    trend_y_max = min(100, trend_df["attendance_pct"].max() + 3)

    line_chart = px.line(
        trend_df,
        x="week_start",
        y="attendance_pct",
        markers=False,
        labels={"week_start": "", "attendance_pct": "Attendance Rate (%)"},
        line_shape="linear",
    )
    line_chart.update_traces(line_color="#4e79a7", line_width=2)

    layout = tableau_base_layout(height=340, margin=dict(l=10, r=20, t=55, b=10))
    layout["yaxis"]["range"]   = [trend_y_min, trend_y_max]
    layout["yaxis"]["title"]   = "Attendance Rate (%)"
    # Override y-axis title to black (user request)
    layout["yaxis"]["title_font"] = dict(color="#1a1a1a", size=12, family=TABLEAU_FONT)
    layout["yaxis"]["showgrid"] = True
    layout["xaxis"]["showgrid"] = False
    layout["xaxis"]["title"]   = ""

    line_chart.update_layout(**layout)
    line_chart.add_hline(y=90, line_dash="dot", line_color=REF_LINE_COLOR, line_width=1.5)
    line_chart.add_annotation(
        text="<b>· · ·  90% Attendance Goal</b>",
        xref="paper", yref="paper",
        x=1.0, y=1.15,
        xanchor="right", yanchor="bottom",
        showarrow=False,
        font=dict(size=11, color=KEYNOTE_COLOR, family=TABLEAU_FONT),
    )

    st.plotly_chart(line_chart, use_container_width=True)


# ── Section 4: Attendance by Program ──────────────────────────────────────────
with st.container(border=True):
    st.subheader("Attendance by Program")

    program_df = metrics["rate_by_program"].copy()
    program_df["attendance_pct"] = program_df["attendance_rate"] * 100

    prog_y_min = max(70, program_df["attendance_pct"].min() - 5)
    prog_y_max = min(100, program_df["attendance_pct"].max() + 4)

    program_bar = go.Figure()
    for i, (_, row) in enumerate(program_df.iterrows()):
        program_bar.add_trace(go.Bar(
            x=[row["program_name"]],
            y=[row["attendance_pct"]],
            name=row["program_name"],
            marker_color=TABLEAU_PALETTE[i % len(TABLEAU_PALETTE)],
            marker_line_width=0,
            text=f"{row['attendance_pct']:.1f}%",
            textposition="outside",
            textfont=dict(color=LABEL_COLOR, size=11, family=TABLEAU_FONT),
            showlegend=False,
        ))

    layout = tableau_base_layout(height=320, margin=dict(l=10, r=20, t=55, b=10))
    layout["yaxis"]["range"]  = [prog_y_min, prog_y_max]
    layout["yaxis"]["title"]  = "Attendance Rate (%)"
    # Override y-axis title to black (user request)
    layout["yaxis"]["title_font"] = dict(color="#1a1a1a", size=12, family=TABLEAU_FONT)
    layout["yaxis"]["showgrid"] = True
    layout["xaxis"]["showgrid"] = False
    layout["xaxis"]["title"]  = ""
    layout["bargap"]          = 0.35

    program_bar.update_layout(**layout)
    program_bar.add_hline(y=90, line_dash="dot", line_color=REF_LINE_COLOR, line_width=1.5)
    program_bar.add_annotation(
        text="<b>· · ·  90% Attendance Goal</b>",
        xref="paper", yref="paper",
        x=1.0, y=1.15,
        xanchor="right", yanchor="bottom",
        showarrow=False,
        font=dict(size=11, color=KEYNOTE_COLOR, family=TABLEAU_FONT),
    )

    st.plotly_chart(program_bar, use_container_width=True)


# ── Section 5: Chronic Absenteeism Table ──────────────────────────────────────
st.markdown("---")
st.subheader(f"Students Needing Attendance Support ({metrics['chronic_count']} students below 90%)")

if metrics["chronic_absentees"].empty:
    st.success("No students are currently flagged for chronic absenteeism. Great work!")
else:
    display_df = metrics["chronic_absentees"][
        ["student_name", "site_name", "program_name", "sessions_attended", "total_sessions", "attendance_rate"]
    ].copy()
    display_df["attendance_rate"] = display_df["attendance_rate"].map(lambda r: f"{r*100:.1f}%")
    display_df = display_df.rename(columns={
        "student_name":      "Student",
        "site_name":         "Site",
        "program_name":      "Program",
        "sessions_attended": "Days Present",
        "total_sessions":    "Total Days",
        "attendance_rate":   "Attendance Rate",
    })

    # Render as plain HTML table so colors are fully controlled —
    # no Streamlit theme interference, guaranteed white bg / black text.
    TABLE_STYLE = """
      width:100%; border-collapse:collapse;
      font-family:'Segoe UI',Arial,sans-serif; font-size:0.88rem;
      background:white; color:#1a1a1a;
    """
    TH_STYLE = """
      background:#f0f0f0; color:#1a1a1a; font-weight:700;
      text-align:left; padding:10px 14px;
      border-bottom:2px solid #d0d0d0; white-space:nowrap;
      position:sticky; top:0; z-index:1;
    """
    TD_STYLE  = "padding:9px 14px; border-bottom:1px solid #e8e8e8; color:#1a1a1a; background:white;"
    TD_ALT    = "padding:9px 14px; border-bottom:1px solid #e8e8e8; color:#1a1a1a; background:#fafafa;"

    header_html = "".join(f'<th style="{TH_STYLE}">{col}</th>' for col in display_df.columns)
    rows_html   = ""
    for idx, row in display_df.iterrows():
        td = TD_ALT if idx % 2 == 0 else TD_STYLE
        cells = "".join(f'<td style="{td}">{val}</td>' for val in row)
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(f"""
    <div style="overflow-x:auto; overflow-y:auto; max-height:400px;
                border:1px solid #d0d0d0; border-radius:4px; background:white;">
      <table style="{TABLE_STYLE}">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    <p style="font-size:0.78rem; color:#555; margin-top:8px;">
      Students below 90% attendance are considered chronically absent by
      standard K-12 guidelines. Early outreach is recommended.
    </p>
    """, unsafe_allow_html=True)


# ── Section 6: Export HTML Report ─────────────────────────────────────────────
st.markdown("---")
st.subheader("Export Summary Report")

st.write(
    "Download a clean, print-ready HTML report to share with your Regional Lead or program team."
)

# Compute a human-readable date range for the report subtitle
date_min = clean_df["date"].min().strftime("%B %d, %Y")
date_max = clean_df["date"].max().strftime("%B %d, %Y")
date_range_string = f"{date_min} – {date_max}"

html_report = generate_html_report(
    metrics,
    date_range   = date_range_string,
    fig_site     = bar_chart,
    fig_trend    = line_chart,
    fig_program  = program_bar,
)

st.download_button(
    label="Download HTML Report",
    data=html_report,
    file_name="attendance_summary_report.html",
    mime="text/html",
)

st.caption(
    "Tip: Open the downloaded file in any web browser to view or print it. "
    "No internet connection required."
)
