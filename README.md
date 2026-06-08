# Student-Attendance-Analytics-Dashboard 📚📚📚
Interactive attendance analytics dashboard for K-12 nonprofit afterschool programs.
Accepts raw attendance CSV data, cleans and processes it, and surfaces key metrics
for Regional Leads and program managers — no spreadsheets required.

## Why this project
Nonprofit program managers need fast, consistent visibility into student attendance
across multiple sites. This dashboard simulates a real program operations loop:
**CSV upload → data cleaning → metric calculation → interactive dashboard → exported report**

## What it does
- Accepts a raw attendance CSV or runs on a built-in synthetic demo dataset (300 students, 5 sites)
- Cleans records automatically: handles missing values, duplicate rows, and mixed date/present formats
- Calculates key metrics:
  - Overall attendance rate vs. 90% goal
  - Attendance rate by site and by program
  - Weekly attendance trend over time
  - Chronic absenteeism flag (below 90%)
- Displays a Tableau-style interactive dashboard with KPI cards, bar charts, and a trend line
- Exports a self-contained, print-ready HTML report with embedded interactive charts

## Tech stack
- Python 3.10+
- Streamlit (dashboard framework)
- pandas (data cleaning and processing)
- Plotly (interactive charts)

---

# Quick Start

## 1) Install dependencies

```bash
pip install -r requirements.txt
```
## 2) Generate the demo dataset
```bash
python data/generate_data.py
```
## 3) Launch the dashboard

```bash
streamlit run app/dashboard.py
```
# Upload Your Own Data

Use the sidebar file uploader to replace the demo dataset with your own CSV.

The file must include the following columns:

| Column | Description | Accepted Values |
|:---|:---|:---|
| `student_id` | Unique student identifier | Any string |
| `student_name` | Full name | Any string |
| `site_name` | Program location | Any string |
| `program_name` | Program type | Any string |
| `date` | Session date | Any standard date format |
| `present` | Attendance status | `1`/`0`, `True`/`False`, `Present`/`Absent` |

Column names are case-insensitive. Extra columns are ignored.

---

# Project Structure
```
attendance-dashboard/
├── app/
│ ├── dashboard.py # Streamlit app — charts, cards, layout
│ ├── data_processor.py # Load, clean, and compute all metrics
│ └── report_exporter.py # Build the downloadable HTML report
├── data/
│ ├── generate_data.py # Synthetic demo dataset generator
│ └── demo_attendance.csv # Pre-built demo (300 students, 5 sites, 3 months)
├── assets/
│ └── dashboard_preview.png
└── requirements.txt
```
---
# How It Works (High Level)
- User uploads a CSV or the app loads the bundled demo dataset on startup
- `data_processor.py` runs a three-stage pipeline: `load_csv()` → `clean_dataframe()` → `compute_metrics()`
- `dashboard.py` renders all visuals using `@st.cache_data` so re-renders stay fast
- Charts are built as live Plotly figures and passed directly to `report_exporter.py`
- The exported HTML report embeds those same figures via `fig.to_html()` — identical to what's on screen
---
# Chronic Absenteeism Definition
A student is flagged as **chronically absent** when their attendance falls below
**90%** of scheduled sessions — the standard K-12 threshold used by the
U.S. Department of Education. Defined in one place and used throughout the pipeline:
```python
# data_processor.py
CHRONIC_ABSENTEEISM_THRESHOLD = 0.90
```
---
## Roadmap

- [ ] Site-level drill-down view with per-student detail
- [ ] Date range filter in the sidebar
- [ ] Automated email report for Regional Leads
- [ ] Connect to a live CSV export from program management systems
- [ ] Multi-year trend comparison

---

## Notes

* **Data Privacy:** No real student data is used — all demo data is fully synthetic.
* **Architecture:** The app is fully file-based; no database or backend server is required.
* **Portability:** The downloaded HTML report works offline once saved (Plotly charts load from CDN).

---

## License

MIT — free to use, adapt, and share.
