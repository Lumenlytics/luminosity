import os
from dotenv import load_dotenv
from supabase import create_client
import pandas as pd

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Get students by grade level
students = supabase.table('students').select('*, grade_levels(label)').execute()
df = pd.DataFrame(students.data)

print("STUDENT ENROLLMENT BY GRADE")
print("=" * 30)
grade_counts = df.groupby('grade_level_id').size()
for grade_id, count in grade_counts.items():
    print(f"Grade {grade_id:2}: {count:3} students")

print(f"\nTotal Students: {len(df)}")