"""
generate_data.py
----------------
Creates a realistic synthetic attendance dataset for demo purposes.
Produces a CSV with ~300 students across 5 program sites over 3 months.

Run this once to create demo_attendance.csv:
    python generate_data.py
"""

import pandas as pd
import numpy as np
import random
from datetime import date, timedelta

# ── Seed for reproducibility ────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

# ── Configuration ───────────────────────────────────────────────────────────
SITES = [
    "Lincoln Elementary",
    "Roosevelt Middle School",
    "Cesar Chavez Academy",
    "Harriet Tubman K-8",
    "Kennedy STEM Magnet",
]

# Each site offers one or two programs
SITE_PROGRAMS = {
    "Lincoln Elementary":       ["After School Enrichment"],
    "Roosevelt Middle School":  ["After School Enrichment", "Tutoring Support"],
    "Cesar Chavez Academy":     ["After School Enrichment"],
    "Harriet Tubman K-8":       ["After School Enrichment", "Homework Help"],
    "Kennedy STEM Magnet":      ["After School Enrichment", "STEM Club"],
}

# Roughly how many students are enrolled at each site
STUDENTS_PER_SITE = {
    "Lincoln Elementary":       55,
    "Roosevelt Middle School":  70,
    "Cesar Chavez Academy":     50,
    "Harriet Tubman K-8":       65,
    "Kennedy STEM Magnet":      60,
}

# Program runs Monday–Friday; we'll generate 3 calendar months
START_DATE = date(2025, 9, 2)   # First Tuesday after Labor Day
END_DATE   = date(2025, 11, 28) # Day before Thanksgiving

# Days off — simplified set of common school holidays
HOLIDAYS = {
    date(2025, 10, 13),  # Columbus Day
    date(2025, 11, 11),  # Veterans Day
    date(2025, 11, 27),  # Thanksgiving eve (program closed)
}

# Each student gets a personal "base attendance probability" so some
# students are naturally more consistent than others.
# Most students cluster around 85–100%; a small tail falls lower (chronic).
ATTENDANCE_MEAN = 0.90
ATTENDANCE_STD  = 0.10


# ── Helper: generate all school days in the date range ──────────────────────
def get_school_days(start: date, end: date, holidays: set) -> list[date]:
    """Return every weekday between start and end that is not a holiday."""
    school_days = []
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in holidays:  # Mon–Fri, not holiday
            school_days.append(current)
        current += timedelta(days=1)
    return school_days


# ── Helper: generate a realistic student name ────────────────────────────────
FIRST_NAMES = [
    "Aaliyah", "Aiden", "Amara", "Andre", "Beatriz", "Brandon", "Chloe",
    "Daniel", "Destiny", "Diego", "Elena", "Elijah", "Emma", "Ethan",
    "Fatima", "Gabriel", "Genesis", "Grace", "Hannah", "Isaiah", "Jasmine",
    "Jaylen", "Jordan", "Jose", "Julian", "Kayla", "Kevin", "Kylie",
    "Layla", "Liam", "Lily", "Luis", "Marcus", "Maria", "Mason",
    "Maya", "Michael", "Miguel", "Mia", "Nathan", "Nicole", "Noah",
    "Olivia", "Omar", "Paige", "Rafael", "Rashida", "Ryan", "Samantha",
    "Santiago", "Sara", "Sofia", "Tiana", "Tyler", "Victor", "Zoe",
]

LAST_NAMES = [
    "Adams", "Alvarez", "Anderson", "Brown", "Carter", "Chen", "Clark",
    "Davis", "Diaz", "Evans", "Flores", "Garcia", "Gonzalez", "Green",
    "Hall", "Harris", "Hernandez", "Hill", "Jackson", "Johnson", "Jones",
    "Kim", "Lee", "Lewis", "Lopez", "Martin", "Martinez", "Miller",
    "Mitchell", "Moore", "Morales", "Nguyen", "Parker", "Patel", "Perez",
    "Ramirez", "Rivera", "Roberts", "Robinson", "Rodriguez", "Sanchez",
    "Scott", "Smith", "Taylor", "Thomas", "Thompson", "Torres", "Turner",
    "Walker", "White", "Williams", "Wilson", "Wright", "Young", "Zhao",
]


def generate_student_name(used_names: set) -> str:
    """Generate a unique full name by drawing from first/last name pools."""
    for _ in range(200):  # try up to 200 times to find a unique combo
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    # Fallback: append a number to guarantee uniqueness
    base = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    suffix = len(used_names)
    return f"{base} {suffix}"


# ── Main generation logic ────────────────────────────────────────────────────
def generate_dataset() -> pd.DataFrame:
    school_days = get_school_days(START_DATE, END_DATE, HOLIDAYS)
    records = []
    student_id_counter = 1001
    used_names: set = set()

    for site, num_students in STUDENTS_PER_SITE.items():
        programs = SITE_PROGRAMS[site]

        for _ in range(num_students):
            student_id   = f"STU{student_id_counter:04d}"
            student_name = generate_student_name(used_names)
            student_id_counter += 1

            # Assign this student to one program at this site
            program = random.choice(programs)

            # Each student has their own attendance probability, clipped 0–1
            attendance_prob = np.clip(
                np.random.normal(ATTENDANCE_MEAN, ATTENDANCE_STD), 0.0, 1.0
            )

            # Generate one row per school day
            for school_day in school_days:
                # Small random day-level noise — students occasionally have
                # "bad weeks" (e.g., illness) modeled as a temporary dip
                daily_noise = np.random.normal(0, 0.05)
                present = int(random.random() < (attendance_prob + daily_noise))

                records.append({
                    "student_id":   student_id,
                    "student_name": student_name,
                    "site_name":    site,
                    "program_name": program,
                    "date":         school_day.isoformat(),  # YYYY-MM-DD string
                    "present":      present,                 # 1 = present, 0 = absent
                })

    return pd.DataFrame(records)


if __name__ == "__main__":
    print("Generating synthetic attendance data...")
    df = generate_dataset()
    output_path = "demo_attendance.csv"
    df.to_csv(output_path, index=False)
    print(f"Done. {len(df):,} records written to {output_path}")
    print(f"  Students : {df['student_id'].nunique()}")
    print(f"  Sites    : {df['site_name'].nunique()}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
