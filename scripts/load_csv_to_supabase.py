print("🚨 Running THE ACTUAL SCRIPT at scripts/load_csv_to_supabase.py")
import os
import pandas as pd
from sqlalchemy import text
from supabase_config import supabase_engine

data_path = "data/clean_csv/"

csv_files = [
    "attendance.csv",
    "assignments.csv",
    "classes.csv",
    "departments.csv",
    "enrollments.csv",
    "fee_types.csv",
    "grade_levels.csv",
    "grade_level_class_map.csv",
    "grades.csv",
    "guardians.csv",
    "guardian_types.csv",
    "payments.csv",
    "periods.csv",
    "school_calendar.csv",
    "standardized_tests.csv",
    "student_guardians.csv",
    "students.csv",
    "teachers.csv",
    "teacher_subjects.csv",
    "student_grade_history.csv"
]

for file in csv_files:
    table_name = file.replace(".csv", "")
    full_path = os.path.join(data_path, file)

    if not os.path.exists(full_path):
        print("SKIPPING " + file + ": File not found at " + full_path)
        continue

    df = pd.read_csv(full_path)

    try:
        print("Uploading " + file + " to table " + table_name + "...")

        with supabase_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE " + table_name + " CASCADE"))

        df.to_sql(table_name, supabase_engine, if_exists="append", index=False, method="multi")

        print("Successfully loaded: " + table_name)

    except Exception as e:
        print("FAILED to load " + table_name + ": " + str(e))
