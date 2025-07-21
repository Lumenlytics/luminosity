#!/usr/bin/env python3
# flake8: noqa
"""
Export all Supabase tables to CSV files for decade expansion analysis

This script connects to your Supabase database and exports all tables
to CSV files in the data/clean_csv directory.

Usage:
    python export_supabase_data.py
"""

import logging
import os

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_supabase_client():
    """Load Supabase client from environment variables"""
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

    return create_client(url, key)


def get_all_tables(supabase: Client):
    """Get list of all tables in the database"""

    # Common Luminosity table names based on your schema
    table_names = [
        "students",
        "teachers",
        "classes",
        "subjects",
        "departments",
        "grade_levels",
        "school_years",
        "terms",
        "periods",
        "classrooms",
        "enrollments",
        "assignments",
        "grades",
        "attendance",
        "guardians",
        "guardian_types",
        "student_guardians",
        "fee_types",
        "payments",
        "discipline_reports",
        "standardized_tests",
        "student_grade_history",
        "teacher_subjects",
        "school_calendar",
        "school_metadata",
    ]

    # Test which tables actually exist
    existing_tables = []
    for table_name in table_names:
        try:
            # Try to get just one record to test if table exists
            result = supabase.table(table_name).select("*").limit(1).execute()
            existing_tables.append(table_name)
            logger.info(f"✅ Found table: {table_name}")
        except Exception as e:
            logger.debug(f"❌ Table {table_name} not found or accessible: {str(e)}")

    logger.info(f"Found {len(existing_tables)} accessible tables")
    return existing_tables


def export_table_to_csv(supabase: Client, table_name: str, output_dir: str):
    """Export a single table to CSV"""
    try:
        # Get all data from the table
        logger.info(f"Exporting {table_name}...")

        # Fetch data in batches to handle large tables
        all_data = []
        offset = 0
        batch_size = 1000

        while True:
            result = (
                supabase.table(table_name)
                .select("*")
                .range(offset, offset + batch_size - 1)
                .execute()
            )

            if not result.data:
                break

            all_data.extend(result.data)
            offset += batch_size

            # Break if we got fewer records than batch size (end of data)
            if len(result.data) < batch_size:
                break

        if not all_data:
            logger.warning(f"Table {table_name} is empty")
            return False

        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(all_data)
        csv_path = os.path.join(output_dir, f"{table_name}.csv")
        df.to_csv(csv_path, index=False)

        logger.info(f"✅ Exported {table_name}: {len(df)} rows → {csv_path}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to export {table_name}: {str(e)}")
        return False


def main():
    """Main export function"""
    try:
        logger.info("Starting Supabase data export...")

        # Create output directory
        output_dir = "../data/clean_csv"
        os.makedirs(output_dir, exist_ok=True)

        # Connect to Supabase
        logger.info("Connecting to Supabase...")
        supabase = load_supabase_client()

        # Get list of tables
        logger.info("Discovering tables...")
        tables = get_all_tables(supabase)

        if not tables:
            logger.error("No accessible tables found!")
            return 1

        # Export each table
        successful_exports = 0
        failed_exports = 0

        for table_name in tables:
            if export_table_to_csv(supabase, table_name, output_dir):
                successful_exports += 1
            else:
                failed_exports += 1

        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("EXPORT COMPLETE")
        logger.info("=" * 50)
        logger.info(f"✅ Successfully exported: {successful_exports} tables")
        logger.info(f"❌ Failed exports: {failed_exports} tables")
        logger.info(f"📁 Files saved to: {output_dir}")

        if successful_exports > 0:
            logger.info("\n🎯 Ready to run decade expansion analysis!")
            logger.info(
                "Next step: python prepare_for_decade_expansion.py --data-dir ./data/clean_csv"
            )

        return 0 if failed_exports == 0 else 1

    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
