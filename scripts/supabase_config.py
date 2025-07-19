import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

# Directly use your full DB connection string
POSTGRES_URL = os.getenv("SUPABASE_DB_URL")

if not POSTGRES_URL:
    raise ValueError("Missing SUPABASE_DB_URL in .env")

# Initialize SQLAlchemy engine
supabase_engine = create_engine(POSTGRES_URL, connect_args={"sslmode": "require"})