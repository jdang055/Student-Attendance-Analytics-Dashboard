"""
report_exporter.py
------------------
Generates a self-contained HTML report that mirrors the dashboard exactly —
same KPI card colors, same Plotly charts, same table styling, same fonts.

The Plotly charts are embedded as interactive HTML using plotly's own
to_html() method. Plotly.js is loaded from CDN so the file stays small.
"""

from datetime import datetime
import pandas as pd


def generate_html_report(
    metrics:     dict,
    date_range:  str  = "",
    fig_site     = None,
    fig_trend    = None,
    fig_program  = None,
) -> str:
    """
    Build and return the full HTML report as a string.

    Parameters
    ----------
    metrics     : dict returned by data_processor.compute_metrics()
    date_range  : human-readable date range string, e.g. "Sep 02, 2025 – Nov 28, 2025"
    fig_site    : Plotly figure for Attendance by Site
    fig_trend   : Plotly figure for Weekly Attendance Trend
    fig_program : Plotly figure for Attendance by Program
    """

    generated_on = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    subtitle     = f"{date_range}&nbsp; &nbsp;|&nbsp; &nbsp;" if date_range else ""

    # ── KPI values ────────────────────────────────────────────────────────────
    overall_pct     = metrics["overall_rate"] * 100
    benchmark_delta = overall_pct - 90.0
    chronic_pct     = metrics["chronic_rate"] * 100

    delta_color = "#2e7a34" if benchmark_delta >= 0 else "#c0392b"
    delta_sign  = "▲" if benchmark_delta >= 0 else "▼"
    support_color = "#c0392b" if metrics["chronic_count"] > 0 else "#2e7a34"

    # ── Embed Plotly charts as HTML divs ──────────────────────────────────────
    # The dashboard figures use tight margins tuned for Streamlit's fluid
    # container. For the fixed-width HTML report we apply generous padding on
    # all sides so axis titles, tick labels, and outside-bar text are never
    # clipped. We work on a deep copy so the live dashboard is unaffected.
    import copy

    REPORT_MARGIN = dict(l=70, r=40, t=70, b=60)   # px — room for titles + keynote

    def chart_div(fig, first: bool = False) -> str:
        if fig is None:
            return '<p style="color:#aaa; font-style:italic;">Chart not available.</p>'
        f = copy.deepcopy(fig)
        f.update_layout(
            margin=REPORT_MARGIN,
            # Let the chart fill the panel width naturally
            autosize=True,
            # Ensure axis titles are visible
            xaxis=dict(title_standoff=12, automargin=True),
            yaxis=dict(title_standoff=12, automargin=True),
        )
        return f.to_html(
            full_html=False,
            include_plotlyjs="cdn" if first else False,
            config={"displayModeBar": False, "responsive": True},
            default_width="100%",   # fill the panel — no fixed pixel width
            default_height="380px",
        )

    chart_site    = chart_div(fig_site,    first=True)
    chart_trend   = chart_div(fig_trend,   first=False)
    chart_program = chart_div(fig_program, first=False)

    # ── Student table rows ────────────────────────────────────────────────────
    def chronic_table_rows(df: pd.DataFrame) -> str:
        if df.empty:
            return '<tr><td colspan="6" style="padding:16px; text-align:center; color:#888;">No students flagged — great work!</td></tr>'
        rows = ""
        display = df[["student_name", "site_name", "program_name",
                       "sessions_attended", "total_sessions", "attendance_rate"]].copy()
        display["attendance_rate"] = display["attendance_rate"].map(lambda r: f"{r*100:.1f}%")
        for i, (_, row) in enumerate(display.iterrows()):
            bg = "#fafafa" if i % 2 == 0 else "white"
            rows += f"""<tr>
              <td style="padding:9px 14px; border-bottom:1px solid #e8e8e8; background:{bg};">{row['student_name']}</td>
              <td style="padding:9px 14px; border-bottom:1px solid #e8e8e8; background:{bg};">{row['site_name']}</td>
              <td style="padding:9px 14px; border-bottom:1px solid #e8e8e8; background:{bg};">{row['program_name']}</td>
              <td style="padding:9px 14px; border-bottom:1px solid #e8e8e8; background:{bg}; text-align:right;">{int(row['sessions_attended'])}</td>
              <td style="padding:9px 14px; border-bottom:1px solid #e8e8e8; background:{bg}; text-align:right;">{int(row['total_sessions'])}</td>
              <td style="padding:9px 14px; border-bottom:1px solid #e8e8e8; background:{bg}; font-weight:600;">{row['attendance_rate']}</td>
            </tr>"""
        return rows

    table_rows = chronic_table_rows(metrics["chronic_absentees"])

    # ── Full HTML ─────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Student Attendance Analytics — Report</title>
  <style>
    /* ── Reset & base ── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f2f2f2;
      color: #1a1a1a;
      padding: 28px 32px 48px;
    }}

    /* ── Page wrapper ── */
    .page {{ max-width: 1100px; margin: 0 auto; }}

    /* ── Title ── */
    .report-title {{
      font-size: 1.9rem;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 4px;
      padding-top: 8px;
    }}
    .report-subtitle {{
      font-size: 0.85rem;
      color: #555;
      margin-bottom: 20px;
    }}

    /* ── KPI row ── */
    .kpi-row {{
      display: flex;
      gap: 12px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }}
    .kpi-card {{
      flex: 1;
      min-width: 180px;
      border-radius: 4px;
      padding: 18px 16px;
      text-align: center;
    }}
    .kpi-card .kpi-label {{
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: #444;
      margin-bottom: 6px;
    }}
    .kpi-card .kpi-value {{
      font-size: 1.9rem;
      font-weight: 700;
      color: #1a1a1a;
      line-height: 1.1;
    }}
    .kpi-card .kpi-sub {{
      font-size: 0.75rem;
      color: #555;
      margin-top: 5px;
    }}

    /* ── Section panels (white card, dashed border) ── */
    .panel {{
      background: white;
      border: 1px dashed #c0c0c0;
      border-radius: 4px;
      padding: 16px 20px 8px;
      margin-bottom: 16px;
    }}
    .panel-title {{
      font-size: 1rem;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 10px;
    }}

    /* ── Student table ── */
    .table-scroll {{
      overflow-x: auto;
      overflow-y: auto;
      max-height: 420px;
      border: 1px solid #d0d0d0;
      border-radius: 4px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    thead th {{
      background: #f0f0f0;
      color: #1a1a1a;
      font-weight: 700;
      text-align: left;
      padding: 10px 14px;
      border-bottom: 2px solid #d0d0d0;
      position: sticky;
      top: 0;
      z-index: 1;
      white-space: nowrap;
    }}
    tbody td {{ color: #1a1a1a; }}

    /* ── Footer ── */
    .footer {{
      text-align: center;
      font-size: 0.78rem;
      color: #aaa;
      margin-top: 24px;
    }}
  </style>
</head>
<body>
<div class="page">

  <!-- Title -->
  <div class="report-title">Student Attendance Analytics</div>
  <div class="report-subtitle">{subtitle}Generated on {generated_on}</div>

  <!-- KPI Cards -->
  <div class="kpi-row">
    <div class="kpi-card" style="background:#aecde8;">
      <div class="kpi-label">Overall Attendance Rate</div>
      <div class="kpi-value">{overall_pct:.1f}%</div>
      <div class="kpi-sub" style="color:{delta_color}; font-weight:600;">
        {delta_sign} {abs(benchmark_delta):.1f}% vs. 90% goal
      </div>
    </div>
    <div class="kpi-card" style="background:#f7c9a3;">
      <div class="kpi-label">Students Enrolled</div>
      <div class="kpi-value">{metrics['total_students']:,}</div>
      <div class="kpi-sub">across all sites</div>
    </div>
    <div class="kpi-card" style="background:#c6deb8;">
      <div class="kpi-label">Attendance Records</div>
      <div class="kpi-value">{metrics['total_sessions']:,}</div>
      <div class="kpi-sub">total sessions tracked</div>
    </div>
    <div class="kpi-card" style="background:#ead8b4;">
      <div class="kpi-label">Students Needing Support</div>
      <div class="kpi-value" style="color:{support_color};">{metrics['chronic_count']}</div>
      <div class="kpi-sub">{chronic_pct:.1f}% of enrolled students</div>
    </div>
  </div>

  <!-- Chart: Attendance by Site -->
  <div class="panel">
    <div class="panel-title">Attendance by Site</div>
    {chart_site}
  </div>

  <!-- Chart: Weekly Attendance Trend -->
  <div class="panel">
    <div class="panel-title">Weekly Attendance Trend</div>
    {chart_trend}
  </div>

  <!-- Chart: Attendance by Program -->
  <div class="panel">
    <div class="panel-title">Attendance by Program</div>
    {chart_program}
  </div>

  <!-- Student Table -->
  <div class="panel">
    <div class="panel-title">
      Students Needing Attendance Support
      ({metrics['chronic_count']} students below 90%)
    </div>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Student</th>
            <th>Site</th>
            <th>Program</th>
            <th style="text-align:right;">Days Present</th>
            <th style="text-align:right;">Total Days</th>
            <th>Attendance Rate</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </div>
    <p style="font-size:0.76rem; color:#666; margin-top:8px;">
      Students below 90% attendance are considered chronically absent by
      standard K-12 guidelines. Early outreach is recommended.
    </p>
  </div>

  <div class="footer">
    Student Attendance Analytics &mdash; For internal use only.
    Please handle student data with care.
  </div>

</div>
</body>
</html>"""

    return html
