import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 🔧 Load credentials from .env or set them directly here
load_dotenv()  # Make sure you have SUPABASE_URL and SUPABASE_KEY in .env

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)  # Format: postgresql://user:password@host:port/db
CONSOLIDATED_FOLDER = "./consolidated"  # path to your folder of CSVs

# 🚀 Create SQLAlchemy engine
engine = create_engine(SUPABASE_URL)

# 🗂 Upload all CSVs in folder
for filename in os.listdir(CONSOLIDATED_FOLDER):
    if filename.endswith(".csv"):
        table_name = filename.replace(".csv", "")
        file_path = os.path.join(CONSOLIDATED_FOLDER, filename)

        print(f"Uploading '{table_name}'...")
        try:
            df = pd.read_csv(file_path)
            df.to_sql(
                table_name, con=engine, if_exists="replace", index=False
            )  # or 'append'
            print(f"✅ Uploaded '{table_name}' ({len(df)} rows)")
        except Exception as e:
            print(f"❌ Failed to upload '{table_name}': {e}")
