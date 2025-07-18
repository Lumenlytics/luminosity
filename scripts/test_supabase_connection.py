import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Connect to Supabase
supabase = create_client(url, key)

try:
    result = supabase.table("periods").select("*").limit(5).execute()
    print("✅ Supabase connection successful.")
    print("📦 Sample result from 'periods':")
    for row in result.data:
        print(row)
except Exception as e:
    print(f"❌ Test failed: {e}")