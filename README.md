# Student-Attendance-Analytics-Dashboard
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
