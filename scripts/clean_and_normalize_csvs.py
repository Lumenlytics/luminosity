import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Load .env credentials
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Use normalized CSVs
csv_folder = os.path.join("data", "normalized_csv")

# List of tables to upload (CSV file name must match table name)
tables = [
    "assignments",
    "attendance",
    "classes",
    "classrooms",
    "departments",
    "discipline_reports",
    "enrollments",
    "fee_types",
    "grade_levels",
    "grades",
    "guardian_types",
    "guardians",
    "payments",
    "periods",
    "school_years",
    "standardized_tests",
    "student_grade_history",
    "student_guardians",
    "students",
    "teacher_subjects",
    "teachers",
    "terms"
]

for table in tables:
    path = os.path.join(csv_folder, f"{table}.csv")
    print(f"Uploading {table}...")

    try:
        df = pd.read_csv(path)

        # Drop empty rows
        df.dropna(how='all', inplace=True)
        if df.empty:
            print(f"⚠️ Skipped {table} — no data.")
            continue

        # Convert NaNs to None for Supabase JSON encoding
        df = df.where(pd.notnull(df), None)

        data = df.to_dict(orient="records")
        supabase.table(table).insert(data).execute()
        print(f"✅ {table} uploaded. Rows: {len(df)}")

    except Exception as e:
        print(f"❌ Failed to upload {table}: {e}")