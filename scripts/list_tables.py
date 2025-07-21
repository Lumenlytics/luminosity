import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Get list of tables
tables = ['students', 'teachers', 'classes', 'grades', 'attendance', 'guardians', 'assignments']

for table in tables:
    try:
        result = supabase.table(table).select('*').limit(1).execute()
        print(f"✅ {table}: {len(result.data)} rows found")
    except Exception as e:
        print(f"❌ {table}: Not found or error")

print("\nReady to work with your Luminosity data!")