#!/usr/bin/env python3
"""
Luminosity School Data Consolidation Script

This script consolidates decade folder structure (2016-2025) into single CSV files
per table for efficient Supabase loading.

Folder Structure Expected:
decade/
├── 2016-2017/
│   ├── students.csv
│   ├── teachers.csv
│   ├── classes.csv
│   └── ...
├── 2017-2018/
│   ├── students.csv
│   └── ...
└── ...

Output: Single consolidated CSV per table with all years combined.
"""

import glob
import logging
import os
from typing import Dict, List

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LuminosityDataConsolidator:
    def __init__(self, decade_folder: str, output_folder: str = "./consolidated_data"):
        self.decade_folder = decade_folder
        self.output_folder = output_folder

        # Expected table names based on YOUR EXACT file structure
        self.expected_tables = [
            "assignments",
            "attendance",
            "calendar",
            "classes",
            "classrooms",
            "departments",
            "discipline_reports",
            "enrollments",
            "fee_types",
            "grades",
            "grade_levels",
            "guardians",
            "guardian_types",
            "payments",
            "periods",
            "school_calendar",
            "school_metadata",
            "school_years",
            "standardized_tests",
            "students",
            "student_grade_history",
            "student_guardians",
            "subjects",
            "teachers",
            "teacher_subjects",
            "terms",
        ]

        # Tables that should be consolidated (contain year-specific data)
        self.tables_to_consolidate = [
            "assignments",
            "attendance",
            "calendar",
            "classes",
            "discipline_reports",
            "enrollments",
            "grades",
            "guardians",
            "payments",
            "school_calendar",
            "school_years",
            "standardized_tests",
            "students",
            "student_grade_history",
            "student_guardians",
            "teachers",
            "teacher_subjects",
            "terms",
        ]

        # Reference tables that are typically static across years
        self.reference_tables = [
            "classrooms",
            "departments",
            "fee_types",
            "grade_levels",
            "guardian_types",
            "periods",
            "school_metadata",
            "subjects",
        ]

        # Year-specific reference tables
        self.yearly_reference_tables = ["terms", "school_years"]

    def discover_school_years(self) -> List[str]:
        """Discover all school year folders in the decade directory."""
        year_folders = []
        for item in os.listdir(self.decade_folder):
            folder_path = os.path.join(self.decade_folder, item)
            if os.path.isdir(folder_path) and "-" in item:
                year_folders.append(item)

        # Sort chronologically
        year_folders.sort()
        logger.info(f"Found school years: {year_folders}")
        return year_folders

    def extract_school_year_id(self, folder_name: str) -> int:
        """Extract school year ID from folder name (e.g., '2016-2017' -> 1, '2017-2018' -> 2)."""
        start_year = int(folder_name.split("-")[0])
        # School year ID starts from 1 for 2016-2017 (first year)
        return start_year - 2015

    def get_csv_files_in_year(self, year_folder: str) -> List[str]:
        """Get all CSV files in a specific year folder."""
        year_path = os.path.join(self.decade_folder, year_folder)
        csv_files = glob.glob(os.path.join(year_path, "*.csv"))
        # Extract table names from simple filenames like "students.csv"
        table_names = [os.path.basename(f).replace(".csv", "") for f in csv_files]
        return table_names

    def add_year_context(
        self, df: pd.DataFrame, table_name: str, school_year_id: int, year_folder: str
    ) -> pd.DataFrame:
        """Add year context to dataframe if needed."""
        df_copy = df.copy()

        # Add school_year_id to tables that need it (ALL consolidation tables)
        if table_name in self.tables_to_consolidate:
            if "school_year_id" not in df_copy.columns:
                df_copy["school_year_id"] = school_year_id

        # Add year metadata for tracking
        if table_name in self.tables_to_consolidate:
            df_copy["data_source_year"] = year_folder

        return df_copy

    def consolidate_table(
        self, table_name: str, year_folders: List[str]
    ) -> pd.DataFrame:
        """Consolidate a single table across all years."""
        consolidated_data = []

        for year_folder in year_folders:
            # Simple filename: table.csv (e.g., students.csv)
            csv_path = os.path.join(
                self.decade_folder, year_folder, f"{table_name}.csv"
            )

            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    school_year_id = self.extract_school_year_id(year_folder)

                    # Add year context
                    df_with_context = self.add_year_context(
                        df, table_name, school_year_id, year_folder
                    )
                    consolidated_data.append(df_with_context)

                    logger.info(f"  {year_folder}: {len(df)} records")

                except Exception as e:
                    logger.error(f"Error reading {csv_path}: {e}")
            else:
                logger.warning(f"Missing {table_name}.csv in {year_folder}")

        if consolidated_data:
            result = pd.concat(consolidated_data, ignore_index=True)

            # Remove duplicate reference data
            if table_name in self.reference_tables:
                # Keep only unique records for reference tables
                key_columns = [col for col in result.columns if col.endswith("_id")]
                if key_columns:
                    result = result.drop_duplicates(subset=key_columns[0], keep="first")

            # Sort by appropriate columns
            if "school_year_id" in result.columns:
                result = result.sort_values(
                    ["school_year_id"]
                    + [col for col in result.columns if col.endswith("_id")][:1]
                )

            return result
        else:
            logger.warning(f"No data found for table: {table_name}")
            return pd.DataFrame()

    def handle_reference_tables(
        self, year_folders: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """Handle reference tables that might be duplicated across years."""
        reference_data = {}

        # For static reference tables, take from the most recent year
        latest_year = year_folders[-1]

        for table_name in self.reference_tables:
            csv_path = os.path.join(
                self.decade_folder, latest_year, f"{table_name}.csv"
            )

            if os.path.exists(csv_path):
                try:
                    df = pd.read_csv(csv_path)
                    reference_data[table_name] = df
                    logger.info(f"Reference table {table_name}: {len(df)} records")
                except Exception as e:
                    logger.error(f"Error reading reference table {csv_path}: {e}")

        return reference_data

    def generate_id_mapping_report(self, consolidated_data: Dict[str, pd.DataFrame]):
        """Generate a report showing ID ranges and potential conflicts."""
        report = []

        for table_name, df in consolidated_data.items():
            if not df.empty:
                id_columns = [
                    col
                    for col in df.columns
                    if col.endswith("_id") and col != "school_year_id"
                ]

                for id_col in id_columns:
                    if id_col in df.columns:
                        min_id = df[id_col].min()
                        max_id = df[id_col].max()
                        unique_count = df[id_col].nunique()
                        total_count = len(df)

                        report.append(
                            {
                                "table": table_name,
                                "id_column": id_col,
                                "min_id": min_id,
                                "max_id": max_id,
                                "unique_ids": unique_count,
                                "total_records": total_count,
                                "has_duplicates": unique_count != total_count,
                            }
                        )

        report_df = pd.DataFrame(report)
        if not report_df.empty:
            report_path = os.path.join(self.output_folder, "id_mapping_report.csv")
            report_df.to_csv(report_path, index=False)
            logger.info(f"ID mapping report saved to: {report_path}")

            # Log any potential issues
            duplicates = report_df[report_df["has_duplicates"] == True]
            if not duplicates.empty:
                logger.warning(
                    f"Tables with duplicate IDs: {duplicates['table'].tolist()}"
                )

    def consolidate_all_data(self) -> Dict[str, pd.DataFrame]:
        """Consolidate all tables from decade folder structure."""
        os.makedirs(self.output_folder, exist_ok=True)

        year_folders = self.discover_school_years()
        if not year_folders:
            logger.error("No school year folders found!")
            return {}

        # Discover what tables exist
        sample_year = year_folders[0]
        available_tables = self.get_csv_files_in_year(sample_year)
        logger.info(f"Available tables: {available_tables}")

        consolidated_data = {}

        # Consolidate main data tables
        for table_name in available_tables:
            if (
                table_name in self.tables_to_consolidate
                or table_name in self.yearly_reference_tables
            ):
                logger.info(f"Consolidating {table_name}...")
                consolidated_df = self.consolidate_table(table_name, year_folders)
                if not consolidated_df.empty:
                    consolidated_data[table_name] = consolidated_df

        # Handle reference tables
        reference_data = self.handle_reference_tables(year_folders)
        consolidated_data.update(reference_data)

        # Generate reports
        self.generate_id_mapping_report(consolidated_data)

        return consolidated_data

    def save_consolidated_data(self, consolidated_data: Dict[str, pd.DataFrame]):
        """Save all consolidated data to CSV files with clean table names."""
        summary_stats = []

        for table_name, df in consolidated_data.items():
            if not df.empty:
                # Use clean table name (e.g., 'students.csv' instead of 'students__2016_2017.csv')
                clean_filename = f"{table_name}.csv"
                output_path = os.path.join(self.output_folder, clean_filename)
                df.to_csv(output_path, index=False)

                stats = {
                    "table": table_name,
                    "total_records": len(df),
                    "columns": list(df.columns),
                    "date_range": self.get_date_range(df),
                    "year_range": self.get_year_range(df),
                }
                summary_stats.append(stats)

                logger.info(f"Saved {clean_filename}: {len(df):,} records")

        # Save summary report
        summary_df = pd.DataFrame(
            [
                {
                    "table": s["table"],
                    "records": s["total_records"],
                    "columns_count": len(s["columns"]),
                    "date_range": s["date_range"],
                    "year_range": s["year_range"],
                }
                for s in summary_stats
            ]
        )

        summary_path = os.path.join(self.output_folder, "consolidation_summary.csv")
        summary_df.to_csv(summary_path, index=False)

        logger.info(f"Consolidation complete! Files saved to: {self.output_folder}")
        logger.info(
            f"Summary: {len(consolidated_data)} tables, {sum(len(df) for df in consolidated_data.values()):,} total records"
        )

    def get_date_range(self, df: pd.DataFrame) -> str:
        """Get date range from dataframe."""
        date_columns = [col for col in df.columns if "date" in col.lower()]
        if date_columns and not df.empty:
            try:
                dates = pd.to_datetime(df[date_columns[0]], errors="coerce").dropna()
                if not dates.empty:
                    return f"{dates.min().strftime('%Y-%m-%d')} to {dates.max().strftime('%Y-%m-%d')}"
            except:
                pass
        return "N/A"

    def get_year_range(self, df: pd.DataFrame) -> str:
        """Get school year range from dataframe."""
        if "school_year_id" in df.columns:
            min_year = df["school_year_id"].min()
            max_year = df["school_year_id"].max()
            return f"Year {min_year} to {max_year}"
        elif "data_source_year" in df.columns:
            years = sorted(df["data_source_year"].unique())
            return f"{years[0]} to {years[-1]}"
        return "N/A"


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Consolidate Luminosity decade data")
    parser.add_argument("--decade-folder", required=True, help="Path to decade folder")
    parser.add_argument(
        "--output-folder", default="./consolidated_data", help="Output folder"
    )

    args = parser.parse_args()

    if not os.path.exists(args.decade_folder):
        logger.error(f"Decade folder not found: {args.decade_folder}")
        return

    # Initialize consolidator
    consolidator = LuminosityDataConsolidator(args.decade_folder, args.output_folder)

    # Consolidate all data
    consolidated_data = consolidator.consolidate_all_data()

    if consolidated_data:
        # Save consolidated data
        consolidator.save_consolidated_data(consolidated_data)

        print("\n" + "=" * 60)
        print("CONSOLIDATION COMPLETE!")
        print("=" * 60)
        print(f"Input folder: {args.decade_folder}")
        print(f"Output folder: {args.output_folder}")
        print(f"Tables processed: {len(consolidated_data)}")
        print(f"Total records: {sum(len(df) for df in consolidated_data.values()):,}")
        print("\nNext steps:")
        print("1. Review the consolidated CSV files")
        print("2. Check the ID mapping report for conflicts")
        print("3. Load into Supabase using your existing schema")
        print("4. Run data validation queries")
    else:
        logger.error("No data was consolidated. Check your folder structure.")


if __name__ == "__main__":
    main()
