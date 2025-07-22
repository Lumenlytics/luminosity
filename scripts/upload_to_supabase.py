#!/usr/bin/env python3
# flake8: noqa
"""
Luminosity School Management System - Supabase Data Uploader

This script uploads all CSV data (baseline 2015-2016 + decade 2016-2025)
to Supabase in the correct order, handling foreign key constraints and
data dependencies.

Usage:
    python upload_to_supabase.py --clean-csv-dir ../data/clean_csv --decade-dir ../data/decade
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LuminositySupabaseUploader:
    """Handles uploading all Luminosity data to Supabase"""

    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "Missing SUPABASE_URL or SUPABASE_KEY environment variables. "
                "Please check your .env file."
            )

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Define table upload order to respect foreign key constraints
        self.table_upload_order = [
            # Independent reference tables first
            "school_metadata",
            "departments",
            "subjects",
            "grade_levels",
            "guardian_types",
            "fee_types",
            "periods",
            "classrooms",
            "school_years",
            # Dependent tables
            "terms",  # depends on school_years
            "school_calendar",  # depends on school_years
            "students",  # depends on grade_levels
            "teachers",  # depends on departments
            "teacher_subjects",  # depends on teachers, subjects, departments
            "guardians",
            "student_guardians",  # depends on students, guardians, guardian_types
            "classes",  # depends on grade_levels, teachers, classrooms, periods, terms
            "enrollments",  # depends on students, classes
            "assignments",  # depends on classes, terms
            "grades",  # depends on students, assignments, terms
            "attendance",  # depends on students
            "discipline_reports",  # depends on students
            "standardized_tests",  # depends on students
            "student_grade_history",  # depends on students, school_years, grade_levels
            "payments",  # depends on guardians, fee_types
        ]

        # Track which tables have been uploaded
        self.uploaded_tables: Set[str] = set()

        # Track total records uploaded
        self.total_records = 0

    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try a simple query to test connection
            result = (
                self.supabase.table("information_schema.tables")
                .select("table_name")
                .limit(1)
                .execute()
            )
            logger.info("✅ Supabase connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            return False

    def create_tables_if_needed(self):
        """Create tables using the enhanced schema if they don't exist"""
        logger.info("Checking if tables need to be created...")

        # Read the enhanced schema
        schema_files = [
            "luminosity_schema_comments.sql",
            "luminosity_schema_comments_part2.sql",
            "luminosity_schema_comments_part3.sql",
        ]

        # For now, we'll assume tables are created manually or via migration
        # In production, you'd want to run the schema files here
        logger.info(
            "ℹ️  Assuming tables already exist. If not, please run the schema files first."
        )

    def clean_dataframe_for_upload(
        self, df: pd.DataFrame, table_name: str
    ) -> pd.DataFrame:
        """Clean DataFrame for Supabase upload"""
        df_clean = df.copy()

        # Handle missing values
        df_clean = df_clean.where(pd.notnull(df_clean), None)

        # Convert boolean columns properly
        boolean_columns = []
        if table_name == "school_calendar":
            boolean_columns = ["is_school_day", "is_holiday"]
        elif table_name == "students":
            # Add any boolean columns for students if they exist
            pass

        for col in boolean_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].astype(bool)

        # Handle date columns - ensure they're in the right format
        date_columns = []
        if table_name in ["students", "teachers"]:
            if "date_of_birth" in df_clean.columns:
                date_columns.append("date_of_birth")
        elif table_name in ["assignments", "grades"]:
            for col in ["due_date", "submitted_on"]:
                if col in df_clean.columns:
                    date_columns.append(col)
        elif table_name == "attendance":
            if "date" in df_clean.columns:
                date_columns.append("date")
        elif table_name in ["school_years", "terms"]:
            for col in ["start_date", "end_date"]:
                if col in df_clean.columns:
                    date_columns.append(col)
        elif table_name == "school_calendar":
            if "calendar_date" in df_clean.columns:
                date_columns.append("calendar_date")
        elif table_name == "payments":
            if "payment_date" in df_clean.columns:
                date_columns.append("payment_date")

        for col in date_columns:
            if col in df_clean.columns:
                # Ensure date format is YYYY-MM-DD
                df_clean[col] = pd.to_datetime(df_clean[col]).dt.strftime("%Y-%m-%d")

        # Remove any columns with leading/trailing spaces
        df_clean.columns = df_clean.columns.str.strip()

        # Handle specific table adjustments
        if table_name == "subjects" and " department_id" in df_clean.columns:
            # Fix the space in column name
            df_clean = df_clean.rename(columns={" department_id": "department_id"})

        if table_name == "grades" and " term_id" in df_clean.columns:
            # Fix the space in column name
            df_clean = df_clean.rename(columns={" term_id": "term_id"})

        return df_clean

    def upload_csv_to_table(
        self, csv_path: str, table_name: str, batch_size: int = 1000
    ) -> bool:
        """Upload a single CSV file to Supabase table"""
        try:
            logger.info(f"📤 Uploading {table_name} from {csv_path}")

            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"   📊 Loaded {len(df)} records")

            if len(df) == 0:
                logger.warning(f"   ⚠️  Empty file, skipping {table_name}")
                return True

            # Clean data
            df_clean = self.clean_dataframe_for_upload(df, table_name)

            # Convert to records for upload
            records = df_clean.to_dict("records")

            # Upload in batches
            total_uploaded = 0
            for i in range(0, len(records), batch_size):
                batch = records[i : i + batch_size]

                try:
                    result = self.supabase.table(table_name).insert(batch).execute()
                    total_uploaded += len(batch)
                    logger.info(
                        f"   ✅ Uploaded batch {i//batch_size + 1}: {len(batch)} records"
                    )

                    # Small delay to avoid rate limiting
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(
                        f"   ❌ Failed to upload batch {i//batch_size + 1}: {e}"
                    )
                    # Try individual records in this batch
                    for record in batch:
                        try:
                            self.supabase.table(table_name).insert([record]).execute()
                            total_uploaded += 1
                        except Exception as e2:
                            logger.error(
                                f"   ❌ Failed to upload individual record: {e2}"
                            )
                            logger.error(f"   🔍 Record: {record}")

            logger.info(
                f"   ✅ Successfully uploaded {total_uploaded}/{len(records)} records to {table_name}"
            )
            self.total_records += total_uploaded
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload {table_name}: {e}")
            return False

    def clear_table(self, table_name: str) -> bool:
        """Clear all data from a table"""
        try:
            # Delete all records
            result = self.supabase.table(table_name).delete().neq("id", 0).execute()
            logger.info(f"🗑️  Cleared table {table_name}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Could not clear table {table_name}: {e}")
            return False

    def find_csv_files(self, directory: str) -> Dict[str, List[str]]:
        """Find all CSV files organized by year"""
        csv_files = {}

        if not os.path.exists(directory):
            logger.warning(f"Directory does not exist: {directory}")
            return csv_files

        # Check if this is the clean_csv directory (baseline data)
        if "clean_csv" in directory or any(
            f.endswith(".csv") for f in os.listdir(directory)
        ):
            # This is a directory with CSV files directly
            csv_files["2015-2016"] = []
            for file in os.listdir(directory):
                if file.endswith(".csv"):
                    csv_files["2015-2016"].append(os.path.join(directory, file))
        else:
            # This is the decade directory with year subdirectories
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    year_files = []
                    for file in os.listdir(item_path):
                        if file.endswith(".csv"):
                            year_files.append(os.path.join(item_path, file))
                    if year_files:
                        csv_files[item] = year_files

        return csv_files

    def upload_year_data(self, year_files: List[str], year_label: str) -> bool:
        """Upload all CSV files for a specific year"""
        logger.info(f"\n{'='*50}")
        logger.info(f"UPLOADING {year_label} DATA")
        logger.info(f"{'='*50}")

        # Group files by table name
        table_files = {}
        for file_path in year_files:
            filename = os.path.basename(file_path)
            table_name = filename.replace(".csv", "")
            table_files[table_name] = file_path

        # Upload in dependency order
        success_count = 0
        for table_name in self.table_upload_order:
            if table_name in table_files:
                if self.upload_csv_to_table(table_files[table_name], table_name):
                    success_count += 1
                    self.uploaded_tables.add(table_name)

        # Upload any remaining tables not in the order list
        for table_name, file_path in table_files.items():
            if table_name not in self.uploaded_tables:
                logger.info(f"📤 Uploading additional table: {table_name}")
                if self.upload_csv_to_table(file_path, table_name):
                    success_count += 1
                    self.uploaded_tables.add(table_name)

        logger.info(
            f"✅ {year_label}: Uploaded {success_count}/{len(table_files)} tables"
        )
        return success_count == len(table_files)

    def upload_all_data(
        self, clean_csv_dir: str, decade_dir: str, clear_existing: bool = False
    ) -> bool:
        """Upload all data from both directories"""
        logger.info("🚀 Starting Luminosity data upload to Supabase")

        # Test connection first
        if not self.test_connection():
            return False

        # Clear existing data if requested
        if clear_existing:
            logger.info("🗑️  Clearing existing data...")
            for table_name in reversed(
                self.table_upload_order
            ):  # Reverse order for deletes
                self.clear_table(table_name)

        success = True

        # Find all CSV files
        clean_files = self.find_csv_files(clean_csv_dir)
        decade_files = self.find_csv_files(decade_dir)

        # Combine and sort by year
        all_files = {**clean_files, **decade_files}
        sorted_years = sorted(all_files.keys())

        logger.info(f"📁 Found data for years: {', '.join(sorted_years)}")

        # Upload each year in chronological order
        for year in sorted_years:
            if not self.upload_year_data(all_files[year], year):
                logger.error(f"❌ Failed to upload {year} data")
                success = False
                # Continue with other years

        # Final summary
        logger.info(f"\n{'='*60}")
        logger.info("UPLOAD SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total records uploaded: {self.total_records:,}")
        logger.info(f"Tables uploaded: {len(self.uploaded_tables)}")
        logger.info(f"Years processed: {len(sorted_years)}")

        if success:
            logger.info("🎉 All data uploaded successfully!")
        else:
            logger.warning("⚠️  Some uploads failed. Check logs for details.")

        return success

    def verify_upload(self) -> Dict[str, int]:
        """Verify data was uploaded correctly by counting records in each table"""
        logger.info("\n🔍 Verifying upload...")

        table_counts = {}
        for table_name in self.uploaded_tables:
            try:
                result = (
                    self.supabase.table(table_name).select("*", count="exact").execute()
                )
                count = result.count
                table_counts[table_name] = count
                logger.info(f"   📊 {table_name}: {count:,} records")
            except Exception as e:
                logger.error(f"   ❌ Could not count {table_name}: {e}")
                table_counts[table_name] = -1

        total_records = sum(count for count in table_counts.values() if count > 0)
        logger.info(f"\n📈 Total records in database: {total_records:,}")

        return table_counts


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Upload all Luminosity CSV data to Supabase"
    )
    parser.add_argument(
        "--clean-csv-dir",
        default="../data/clean_csv",
        help="Directory containing baseline 2015-2016 CSV files",
    )
    parser.add_argument(
        "--decade-dir",
        default="../data/decade",
        help="Directory containing decade data (2016-2025 subdirectories)",
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing data before upload",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing data, do not upload",
    )

    args = parser.parse_args()

    # Check if directories exist
    if not os.path.exists(args.clean_csv_dir):
        logger.error(f"Clean CSV directory does not exist: {args.clean_csv_dir}")
        sys.exit(1)

    if not os.path.exists(args.decade_dir):
        logger.error(f"Decade directory does not exist: {args.decade_dir}")
        sys.exit(1)

    # Initialize uploader
    try:
        uploader = LuminositySupabaseUploader()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    if args.verify_only:
        # Just verify existing data
        uploader.verify_upload()
    else:
        # Upload all data
        success = uploader.upload_all_data(
            args.clean_csv_dir, args.decade_dir, clear_existing=args.clear_existing
        )

        if success:
            # Verify the upload
            uploader.verify_upload()
            logger.info(
                "\n🎓 Luminosity data upload complete! Ready for dashboard development."
            )
        else:
            logger.error("💥 Upload failed. Please check the logs and try again.")
            sys.exit(1)


if __name__ == "__main__":
    main()
