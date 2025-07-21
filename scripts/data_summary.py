import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

tables = ['students', 'teachers', 'classes', 'grades', 'attendance', 'guardians', 
          'assignments', 'classrooms', 'departments', 'discipline_reports', 
          'enrollments', 'fee_types', 'grade_levels', 'guardian_types', 
          'payments', 'periods', 'school_calendar', 'school_metadata', 
          'school_years', 'standardized_tests', 'student_grade_history', 
          'student_guardians', 'subjects', 'teacher_subjects', 'terms']

print("LUMINOSITY DATABASE SUMMARY")
print("=" * 40)

for table in tables:
    try:
        result = supabase.table(table).select('*', count='exact').execute()
        count = result.count
        print(f"{table:12}: {count:,} records")
    except Exception as e:
        print(f"{table:12}: Error - {e}")