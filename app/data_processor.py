"""
data_processor.py
-----------------
Loads a raw attendance CSV, cleans it, and computes all the metrics
the dashboard and report need.

This module is intentionally separate from the dashboard so that the
data logic can be tested or reused without Streamlit running.
"""

import pandas as pd
import numpy as np

# ── Constants ────────────────────────────────────────────────────────────────
CHRONIC_ABSENTEEISM_THRESHOLD = 0.90  # Below 90% = chronically absent

REQUIRED_COLUMNS = {
    "student_id",
    "student_name",
    "site_name",
    "program_name",
    "date",
    "present",
}


# ── Step 1: Load & Validate ───────────────────────────────────────────────────
def load_csv(filepath_or_buffer) -> pd.DataFrame:
    """
    Read a CSV file (path string or file-like object from Streamlit uploader).
    Raises a clear ValueError if required columns are missing.
    """
    df = pd.read_csv(filepath_or_buffer)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {', '.join(sorted(missing))}\n"
            f"Found columns: {', '.join(df.columns)}"
        )
    return df


# ── Step 2: Clean ─────────────────────────────────────────────────────────────
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize and repair the raw dataframe:
    - Parse dates into proper date objects
    - Normalize the 'present' column to integer 0/1
    - Strip whitespace from text fields
    - Drop exact duplicate rows
    - Drop rows where essential fields are null
    """
    df = df.copy()

    # ── Text fields: strip leading/trailing whitespace ───────────────────────
    for column in ["student_id", "student_name", "site_name", "program_name"]:
        df[column] = df[column].astype(str).str.strip()

    # ── Dates: coerce anything parseable, drop rows that can't be parsed ──────
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    unparseable_date_count = df["date"].isna().sum()
    if unparseable_date_count > 0:
        df = df.dropna(subset=["date"])

    # ── Present column: accept 1/0, True/False, "Present"/"Absent" ───────────
    df["present"] = df["present"].astype(str).str.strip().str.lower()
    presence_map = {
        "1": 1, "true": 1, "yes": 1, "present": 1,
        "0": 0, "false": 0, "no": 0, "absent": 0,
    }
    df["present"] = df["present"].map(presence_map)

    # Drop rows where 'present' couldn't be interpreted
    df = df.dropna(subset=["present"])
    df["present"] = df["present"].astype(int)

    # ── Drop exact duplicates (same student, same date) ───────────────────────
    df = df.drop_duplicates(subset=["student_id", "date"])

    # ── Add a week-start column for weekly trend grouping ─────────────────────
    # "W-MON" snaps each date back to the Monday of its week
    df["week_start"] = df["date"] - pd.to_timedelta(df["date"].dt.dayofweek, unit="D")

    return df.reset_index(drop=True)


# ── Step 3: Compute Metrics ───────────────────────────────────────────────────
def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Return a dictionary of all computed metrics.
    Each value is either a scalar, a Series, or a DataFrame — whatever
    the dashboard needs to render each widget.
    """
    metrics = {}

    # ── Overall attendance rate ───────────────────────────────────────────────
    metrics["overall_rate"] = df["present"].mean()

    # ── Total unique students and total sessions ──────────────────────────────
    metrics["total_students"] = df["student_id"].nunique()
    metrics["total_sessions"] = len(df)

    # ── Attendance rate by site ───────────────────────────────────────────────
    metrics["rate_by_site"] = (
        df.groupby("site_name")["present"]
        .mean()
        .reset_index()
        .rename(columns={"present": "attendance_rate"})
        .sort_values("attendance_rate", ascending=False)
    )

    # ── Attendance rate by program ────────────────────────────────────────────
    metrics["rate_by_program"] = (
        df.groupby("program_name")["present"]
        .mean()
        .reset_index()
        .rename(columns={"present": "attendance_rate"})
        .sort_values("attendance_rate", ascending=False)
    )

    # ── Weekly attendance trend ───────────────────────────────────────────────
    metrics["weekly_trend"] = (
        df.groupby("week_start")["present"]
        .mean()
        .reset_index()
        .rename(columns={"present": "attendance_rate"})
        .sort_values("week_start")
    )

    # ── Per-student rates for chronic absenteeism detection ───────────────────
    student_rates = (
        df.groupby(["student_id", "student_name", "site_name", "program_name"])
        .agg(
            sessions_attended=("present", "sum"),
            total_sessions=("present", "count"),
        )
        .reset_index()
    )
    student_rates["attendance_rate"] = (
        student_rates["sessions_attended"] / student_rates["total_sessions"]
    )

    metrics["student_rates"] = student_rates

    # ── Chronically absent students ───────────────────────────────────────────
    metrics["chronic_absentees"] = (
        student_rates[student_rates["attendance_rate"] < CHRONIC_ABSENTEEISM_THRESHOLD]
        .sort_values("attendance_rate")
        .reset_index(drop=True)
    )

    metrics["chronic_count"] = len(metrics["chronic_absentees"])
    metrics["chronic_rate"] = (
        metrics["chronic_count"] / metrics["total_students"]
        if metrics["total_students"] > 0
        else 0.0
    )

    return metrics


# ── Public entry point ────────────────────────────────────────────────────────
def process_attendance_file(filepath_or_buffer) -> tuple[pd.DataFrame, dict]:
    """
    Full pipeline: load → clean → compute metrics.
    Returns the cleaned DataFrame and the metrics dictionary.
    """
    raw_df   = load_csv(filepath_or_buffer)
    clean_df = clean_dataframe(raw_df)
    metrics  = compute_metrics(clean_df)
    return clean_df, metrics
