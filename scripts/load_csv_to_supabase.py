import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pathlib import Path

# Load environment variables
load_dotenv()

# Get DB URL from .env
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
if not SUPABASE_DB_URL:
    raise ValueError("SUPABASE_DB_URL not found in .env file")

# Create SQLAlchemy engine
engine = create_engine(SUPABASE_DB_URL)

# Folder containing cleaned CSVs
csv_folder = Path("data/clean_csv")

# Tables to upload (add/remove as needed)
tables = [
    "assignments",
    # "attendance",
    # "classes",
    # Add more here as you verify schemas
]

def load_table(table_name):
    csv_path = csv_folder / f"{table_name}.csv"
    if not csv_path.exists():
        print(f"❌ CSV not found for table: {table_name}")
        return

    try:
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"✅ Uploaded: {table_name}")
    except Exception as e:
        print(f"❌ Failed to upload {table_name}: {e}")

if __name__ == "__main__":
    for table in tables:
        load_table(table)