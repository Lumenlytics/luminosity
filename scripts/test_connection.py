import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Test connection
result = supabase.table('students').select('*').limit(5).execute()
print(f"Connection successful! Found {len(result.data)} students")
print(result.data)