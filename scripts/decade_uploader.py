#!/usr/bin/env python3
# flake8: noqa
"""
Luminosity Decade Data Uploader

This script combines multiple year folders into a single dataset and uploads to Supabase.
It looks for decade data in folders like 2016-2017, 2017-2018, etc. and combines them
into single CSV files before uploading.

Usage (run from scripts/ folder):
    cd scripts
    python decade_uploader.py

Or with custom options:
    python decade_uploader.py --decade-dir ../data/decade --batch-size 500

Requirements:
    pip install supabase pandas python-dotenv tqdm
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from tqdm import tqdm

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Supabase imports
try:
    from dotenv import load_dotenv
    from supabase import Client, create_client
except ImportError:
    print("❌ Missing required packages. Please install:")
    print("pip install supabase pandas python-dotenv tqdm")
    sys.exit(1)

# Configure logging
script_dir = Path(__file__).parent
log_file = script_dir / f'decade_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class DecadeDataCombiner:
    """Combines multiple year folders into single CSV files"""

    def __init__(self, decade_dir: Path):
        self.decade_dir = decade_dir
        self.year_folders = []
        self.combined_data = {}

    def discover_year_folders(self):
        """Find all year folders in the decade directory"""
        if not self.decade_dir.exists():
            logger.error(f"Decade directory not found: {self.decade_dir}")
            return []

        # Look for folders matching year patterns like 2016-2017, 2017-2018, etc.
        year_folders = []
        for folder in self.decade_dir.iterdir():
            if folder.is_dir() and "-" in folder.name:
                try:
                    # Check if folder name looks like YYYY-YYYY
                    years = folder.name.split("-")
                    if len(years) == 2 and all(
                        len(y) == 4 and y.isdigit() for y in years
                    ):
                        year_folders.append(folder)
                except:
                    continue

        # Sort by year
        year_folders.sort(key=lambda f: f.name)
        self.year_folders = year_folders

        logger.info(f"Found {len(year_folders)} year folders:")
        for folder in year_folders:
            logger.info(f"  📁 {folder.name}")

        return year_folders

    def get_all_table_names(self):
        """Get all unique table names across all year folders"""
        table_names = set()

        for year_folder in self.year_folders:
            csv_files = list(year_folder.glob("*.csv"))
            for csv_file in csv_files:
                table_name = csv_file.stem  # filename without extension
                table_names.add(table_name)

        return sorted(list(table_names))

    def combine_table_data(self, table_name: str) -> pd.DataFrame:
        """Combine data for a specific table across all years"""
        combined_dfs = []

        logger.info(
            f"📋 Combining {table_name} data across {len(self.year_folders)} years..."
        )

        for year_folder in self.year_folders:
            csv_file = year_folder / f"{table_name}.csv"

            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file)
                    if len(df) > 0:
                        # Add year information for tracking
                        df["source_year_folder"] = year_folder.name
                        combined_dfs.append(df)
                        logger.info(f"    ✅ {year_folder.name}: {len(df)} records")
                    else:
                        logger.warning(f"    ⚠️ {year_folder.name}: Empty file")
                except Exception as e:
                    logger.error(
                        f"    ❌ {year_folder.name}: Failed to read - {str(e)}"
                    )
            else:
                logger.warning(f"    ⚠️ {year_folder.name}: File not found")

        if combined_dfs:
            # Combine all dataframes
            combined_df = pd.concat(combined_dfs, ignore_index=True)

            # Remove the tracking column before returning
            if "source_year_folder" in combined_df.columns:
                combined_df = combined_df.drop("source_year_folder", axis=1)

            # Remove duplicates based on primary key if we can identify it
            combined_df = self._remove_duplicates(table_name, combined_df)

            logger.info(f"✅ Combined {table_name}: {len(combined_df)} total records")
            return combined_df
        else:
            logger.warning(f"⚠️ No data found for {table_name}")
            return pd.DataFrame()

    def _remove_duplicates(self, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicates based on likely primary keys"""
        # Define likely primary key columns for each table
        primary_keys = {
            "students": ["student_id"],
            "teachers": ["teacher_id"],
            "classes": ["class_id"],
            "assignments": ["assignment_id"],
            "grades": ["grade_id"],
            "attendance": ["attendance_id"],
            "enrollments": ["enrollment_id"],
            "school_calendar": ["calendar_date"],
            "school_years": ["school_year_id"],
            "terms": ["term_id"],
            "subjects": ["subject_id"],
            "departments": ["department_id"],
            "guardians": ["guardian_id"],
            "student_guardians": ["student_id", "guardian_id"],
            "teacher_subjects": ["teacher_id", "subject_id"],
            "payments": ["payment_id"],
            "discipline_reports": ["discipline_report_id"],
            "standardized_tests": ["test_id"],
            "student_grade_history": ["student_grade_history_id"],
            "grade_levels": ["grade_level_id"],
            "guardian_types": ["guardian_type_id"],
            "fee_types": ["fee_type_id"],
            "periods": ["period_id"],
            "classrooms": ["classroom_id"],
            "school_metadata": ["school_name"],  # Assuming school name is unique
        }

        if table_name in primary_keys:
            key_cols = primary_keys[table_name]
            # Check if all key columns exist
            existing_key_cols = [col for col in key_cols if col in df.columns]

            if existing_key_cols:
                initial_count = len(df)
                df = df.drop_duplicates(
                    subset=existing_key_cols, keep="last"
                )  # Keep most recent
                final_count = len(df)

                if initial_count != final_count:
                    logger.info(
                        f"    🔄 Removed {initial_count - final_count} duplicates from {table_name}"
                    )

        return df

    def combine_all_data(self) -> Dict[str, pd.DataFrame]:
        """Combine data for all tables"""
        logger.info("🔄 Starting decade data combination...")

        if not self.discover_year_folders():
            logger.error("No year folders found!")
            return {}

        table_names = self.get_all_table_names()
        logger.info(f"Found {len(table_names)} unique tables: {', '.join(table_names)}")

        combined_data = {}

        for table_name in table_names:
            df = self.combine_table_data(table_name)
            if len(df) > 0:
                combined_data[table_name] = df

        logger.info(f"✅ Successfully combined {len(combined_data)} tables")
        return combined_data

    def save_combined_data(
        self, combined_data: Dict[str, pd.DataFrame], output_dir: Path
    ):
        """Save combined data to CSV files"""
        output_dir.mkdir(exist_ok=True)

        logger.info(f"💾 Saving combined data to {output_dir}")

        for table_name, df in combined_data.items():
            output_file = output_dir / f"{table_name}.csv"
            df.to_csv(output_file, index=False)
            logger.info(f"    ✅ Saved {table_name}.csv ({len(df)} records)")


class LuminosityDecadeUploader:
    """Upload combined decade data to Supabase"""

    def __init__(self, supabase_url: str, supabase_key: str, batch_size: int = 1000):
        """Initialize the Supabase uploader."""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.batch_size = batch_size
        self.upload_stats = {
            "tables_processed": 0,
            "total_records": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "start_time": datetime.now(),
        }

        # Define table upload order based on foreign key dependencies
        self.upload_order = [
            # Reference tables (no dependencies)
            "school_metadata",
            "departments",
            "grade_levels",
            "guardian_types",
            "fee_types",
            "periods",
            "classrooms",
            "school_years",
            "standardized_test_types",
            # Tables with single dependencies
            "terms",
            "subjects",
            "teachers",
            "guardians",
            "students",
            "school_calendar",
            # Tables with multiple dependencies
            "teacher_subjects",
            "classes",
            "student_guardians",
            # High-dependency tables
            "enrollments",
            "assignments",
            "grades",
            "attendance",
            "discipline_reports",
            "standardized_tests",
            "student_grade_history",
            "payments",
            # Optional/mapping tables
            "grade_level_class_map",
        ]

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess DataFrame before upload (same as original script)"""
        # Handle common data type issues
        # Convert date columns
        date_columns = [
            "date",
            "due_date",
            "submitted_on",
            "payment_date",
            "test_date",
            "start_date",
            "end_date",
            "calendar_date",
            "date_of_birth",
            "assigned_date",
        ]

        for col in date_columns:
            if col in df.columns:
                # Convert to string format instead of date objects
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime(
                    "%Y-%m-%d"
                )

        # Handle boolean columns
        boolean_columns = ["is_school_day", "is_holiday", "is_active", "is_current"]
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)

        # Handle null values appropriately
        df = df.where(pd.notnull(df), None)

        # Remove unnamed columns (pandas artifacts)
        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

        return df

    def upload_table_batch(
        self, table_name: str, data: List[Dict], batch_num: int = 0
    ) -> bool:
        """Upload a batch of data to a specific table (same as original script)"""
        try:
            # Convert pandas/numpy types to Python native types
            clean_data = []
            for record in data:
                clean_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        clean_record[key] = None
                    elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                        clean_record[key] = str(value)
                    elif hasattr(value, "strftime"):  # Any date-like object
                        clean_record[key] = (
                            value.strftime("%Y-%m-%d")
                            if hasattr(value, "year")
                            else str(value)
                        )
                    elif hasattr(value, "item"):  # numpy types
                        clean_record[key] = value.item()
                    else:
                        clean_record[key] = value
                clean_data.append(clean_record)

            # Attempt upload with UPSERT to handle existing records
            result = self.supabase.table(table_name).upsert(clean_data).execute()

            if result.data:
                self.upload_stats["successful_uploads"] += len(clean_data)
                logger.info(
                    f"✅ Uploaded batch {batch_num} to {table_name}: {len(clean_data)} records"
                )
                return True
            else:
                logger.error(
                    f"❌ Upload failed for {table_name} batch {batch_num}: No data returned"
                )
                return False

        except Exception as e:
            logger.error(
                f"❌ Upload failed for {table_name} batch {batch_num}: {str(e)}"
            )
            self.upload_stats["failed_uploads"] += len(data)
            return False

    def upload_table(self, table_name: str, df: pd.DataFrame) -> bool:
        """Upload an entire table with batch processing (same as original script)"""
        total_records = len(df)
        logger.info(f"📤 Uploading {table_name}: {total_records} records")

        if total_records == 0:
            logger.warning(f"⚠️ No data to upload for {table_name}")
            return True

        # Preprocess the data
        df = self.preprocess_dataframe(df)

        # Convert DataFrame to list of dictionaries
        records = df.to_dict("records")

        # Upload in batches
        successful_batches = 0
        total_batches = (total_records + self.batch_size - 1) // self.batch_size

        with tqdm(total=total_batches, desc=f"Uploading {table_name}") as pbar:
            for i in range(0, total_records, self.batch_size):
                batch = records[i : i + self.batch_size]
                batch_num = i // self.batch_size + 1

                if self.upload_table_batch(table_name, batch, batch_num):
                    successful_batches += 1

                pbar.update(1)

        success_rate = successful_batches / total_batches
        if success_rate >= 0.95:  # 95% success rate threshold
            logger.info(
                f"✅ Successfully uploaded {table_name} ({success_rate:.1%} success rate)"
            )
            return True
        else:
            logger.error(
                f"❌ Upload failed for {table_name} ({success_rate:.1%} success rate)"
            )
            return False

    def clear_table(self, table_name: str) -> bool:
        """Clear all data from a table (use with caution!)"""
        try:
            result = self.supabase.table(table_name).delete().neq("id", -1).execute()
            logger.info(f"🗑️ Cleared table {table_name}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Could not clear table {table_name}: {str(e)}")
            return True

    def upload_combined_data(
        self, combined_data: Dict[str, pd.DataFrame], clear_existing: bool = False
    ) -> Dict:
        """Upload all combined data to Supabase"""
        logger.info("🚀 Starting decade dataset upload to Supabase")
        logger.info(f"📦 Batch size: {self.batch_size}")
        logger.info(f"📊 Tables to upload: {len(combined_data)}")

        results = {
            "successful_tables": [],
            "failed_tables": [],
            "verification_results": {},
        }

        # Process tables in dependency order
        for table_name in self.upload_order:
            if table_name not in combined_data:
                logger.warning(
                    f"⚠️ Table {table_name} not found in combined data, skipping"
                )
                continue

            try:
                # Clear existing data if requested
                if clear_existing:
                    self.clear_table(table_name)

                # Upload data
                df = combined_data[table_name]

                if self.upload_table(table_name, df):
                    results["successful_tables"].append(table_name)
                else:
                    results["failed_tables"].append(table_name)

                self.upload_stats["tables_processed"] += 1
                self.upload_stats["total_records"] += len(df)

            except Exception as e:
                logger.error(f"❌ Failed to process {table_name}: {str(e)}")
                results["failed_tables"].append(table_name)

        # Generate final report
        self.generate_upload_report(results)
        return results

    def generate_upload_report(self, results: Dict):
        """Generate a comprehensive upload report"""
        end_time = datetime.now()
        duration = end_time - self.upload_stats["start_time"]

        report_file = (
            script_dir
            / f'decade_upload_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        )

        report = f"""
{'='*60}
🎯 LUMINOSITY DECADE UPLOAD REPORT
{'='*60}

⏱️  Duration: {duration}
📊 Tables Processed: {self.upload_stats['tables_processed']}
📝 Total Records: {self.upload_stats['total_records']:,}
✅ Successful Uploads: {self.upload_stats['successful_uploads']:,}
❌ Failed Uploads: {self.upload_stats['failed_uploads']:,}

📈 SUCCESS RATE: {(self.upload_stats['successful_uploads'] / max(self.upload_stats['total_records'], 1)) * 100:.1f}%

{'='*30}
SUCCESSFUL TABLES ({len(results['successful_tables'])})
{'='*30}
"""
        for table in results["successful_tables"]:
            report += f"✅ {table}\n"

        if results["failed_tables"]:
            report += f"""
{'='*30}
FAILED TABLES ({len(results['failed_tables'])})
{'='*30}
"""
            for table in results["failed_tables"]:
                report += f"❌ {table}\n"

        report += f"""
{'='*60}
🎉 Decade Upload Complete! Your 10-year Luminosity dataset is now in Supabase!
📄 Log saved to: {log_file}
📄 Report saved to: {report_file}
{'='*60}
"""

        logger.info(report)

        # Save report to file
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"📄 Report saved to: {report_file}")


def main():
    """Main function to run the decade upload process"""
    parser = argparse.ArgumentParser(
        description="Combine and upload Luminosity decade data to Supabase"
    )
    parser.add_argument(
        "--decade-dir",
        default="../data/decade",
        help="Directory containing year folders (e.g., 2016-2017, 2017-2018, etc.)",
    )
    parser.add_argument(
        "--output-dir",
        default="../data/combined_csv",
        help="Directory to save combined CSV files",
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Batch size for uploads"
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing data before upload (DANGEROUS!)",
    )
    parser.add_argument(
        "--env-file",
        default="../.env",
        help="Path to .env file with Supabase credentials",
    )
    parser.add_argument(
        "--combine-only",
        action="store_true",
        help="Only combine data, don't upload to Supabase",
    )

    args = parser.parse_args()

    # Convert relative paths to absolute paths from script location
    script_dir = Path(__file__).parent
    decade_dir = (script_dir / args.decade_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()
    env_file = (script_dir / args.env_file).resolve()

    # Step 1: Combine decade data
    logger.info("=" * 60)
    logger.info("🎓 LUMINOSITY DECADE DATA PROCESSOR")
    logger.info("=" * 60)

    combiner = DecadeDataCombiner(decade_dir)
    combined_data = combiner.combine_all_data()

    if not combined_data:
        logger.error("❌ No data to process!")
        sys.exit(1)

    # Save combined data
    combiner.save_combined_data(combined_data, output_dir)

    if args.combine_only:
        logger.info("✅ Data combination complete! Use --upload to upload to Supabase.")
        sys.exit(0)

    # Step 2: Upload to Supabase
    logger.info("\n" + "=" * 60)
    logger.info("🚀 UPLOADING TO SUPABASE")
    logger.info("=" * 60)

    # Load environment variables
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"📄 Loaded environment from: {env_file}")
    else:
        logger.warning(f"⚠️ Environment file not found: {env_file}")
        load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("❌ Missing Supabase credentials in environment variables")
        logger.error("Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
        sys.exit(1)

    # Initialize uploader and start process
    uploader = LuminosityDecadeUploader(supabase_url, supabase_key, args.batch_size)

    try:
        results = uploader.upload_combined_data(combined_data, args.clear_existing)

        if len(results["failed_tables"]) == 0:
            logger.info(
                "🎉 ALL UPLOADS SUCCESSFUL! Your decade dataset is ready in Supabase!"
            )
            sys.exit(0)
        else:
            logger.error("⚠️ Some uploads failed. Check logs for details.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"💥 Upload process failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
