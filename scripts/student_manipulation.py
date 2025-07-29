#!/usr/bin/env python3
"""
Luminosity Grade Level Redistribution Script

This script takes roughly half of the grade_level_id = 1 students
and converts them to grade_level_id = 0 (kindergarten) by:
1. Randomly selecting ~50% of 1st graders from each school year
2. Changing their grade_level_id from 1 to 0
3. Subtracting 1 year from their date_of_birth
4. Modifying the students.csv file directly
"""

import random
import sys
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd


def subtract_year_from_date(date_string: str) -> str:
    """Subtract one year from a date string in YYYY-MM-DD format"""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        new_date = date_obj.replace(year=date_obj.year - 1)
        return new_date.strftime("%Y-%m-%d")
    except ValueError:
        print(f"⚠️  Warning: Invalid date format '{date_string}', skipping modification")
        return date_string


def redistribute_grade_levels(
    csv_file_path: str = "../data/clean_csv/students.csv",
) -> None:
    """
    Main function to redistribute grade levels from 1st grade to kindergarten

    Args:
        csv_file_path: Path to the students.csv file
    """
    print("🚀 Starting Grade Level Redistribution...\n")

    try:
        # Read the students.csv file
        print(f"📖 Reading {csv_file_path}...")
        df = pd.read_csv(csv_file_path)

        print(f"✅ Loaded {len(df)} student records\n")

        # Validate required columns exist
        required_columns = [
            "student_id",
            "grade_level_id",
            "school_year_id",
            "date_of_birth",
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Track changes for reporting
        changes_summary: Dict[int, Dict[str, Any]] = {}
        total_changes = 0

        # Get all unique school years
        school_years = sorted(df["school_year_id"].unique())

        print("📊 BEFORE Modification:")
        print("========================")

        # Show before counts and prepare for changes
        for year_id in school_years:
            year_data = df[df["school_year_id"] == year_id]
            first_graders = year_data[year_data["grade_level_id"] == 1]
            kindergarteners = year_data[year_data["grade_level_id"] == 0]

            num_to_move = len(first_graders) // 2  # Roughly half

            changes_summary[year_id] = {
                "before": {
                    "kindergarten": len(kindergarteners),
                    "first_grade": len(first_graders),
                },
                "to_move": num_to_move,
            }

            print(
                f"School Year {year_id}: K={len(kindergarteners)}, 1st={len(first_graders)} → Moving {num_to_move} to K"
            )

        print("\n🔄 Processing changes...\n")

        # Set random seed for reproducibility (optional - remove if you want different results each run)
        random.seed(42)

        # Process each school year
        for year_id in school_years:
            # Get indices of all 1st graders for this school year
            first_grade_mask = (df["school_year_id"] == year_id) & (
                df["grade_level_id"] == 1
            )
            first_grade_indices = df[first_grade_mask].index.tolist()

            # Randomly select roughly half to move to kindergarten
            num_to_move = changes_summary[year_id]["to_move"]

            if num_to_move > 0:
                # Randomly sample indices
                indices_to_move = random.sample(first_grade_indices, num_to_move)

                # Apply changes to these students
                for idx in indices_to_move:
                    # Change grade level to 0 (kindergarten)
                    df.at[idx, "grade_level_id"] = 0

                    # Subtract 1 year from birth date
                    original_date = df.at[idx, "date_of_birth"]
                    df.at[idx, "date_of_birth"] = subtract_year_from_date(
                        str(original_date)
                    )

                    total_changes += 1

            print(f"✅ School Year {year_id}: Modified {num_to_move} students")

        # Show after counts
        print("\n📊 AFTER Modification:")
        print("=======================")

        for year_id in school_years:
            year_data = df[df["school_year_id"] == year_id]
            first_graders = year_data[year_data["grade_level_id"] == 1]
            kindergarteners = year_data[year_data["grade_level_id"] == 0]

            changes_summary[year_id]["after"] = {
                "kindergarten": len(kindergarteners),
                "first_grade": len(first_graders),
            }

            k_change = (
                changes_summary[year_id]["after"]["kindergarten"]
                - changes_summary[year_id]["before"]["kindergarten"]
            )
            first_change = (
                changes_summary[year_id]["before"]["first_grade"]
                - changes_summary[year_id]["after"]["first_grade"]
            )

            print(
                f"School Year {year_id}: K={len(kindergarteners)} (+{k_change}), 1st={len(first_graders)} (-{first_change})"
            )

        # Write the modified data back to the CSV file
        print(f"\n💾 Writing modified data back to {csv_file_path}...")
        df.to_csv(csv_file_path, index=False)

        # Final summary
        print("\n🎉 REDISTRIBUTION COMPLETE!")
        print("============================")
        print(f"Total students modified: {total_changes}")
        print(f"Total records in file: {len(df)}")

        # Show summary table
        print("\n📋 Summary by School Year:")
        print("School Year | K Before → After | 1st Before → After | Students Moved")
        print("------------|------------------|-------------------|---------------")

        for year_id in school_years:
            summary = changes_summary[year_id]
            k_before = summary["before"]["kindergarten"]
            k_after = summary["after"]["kindergarten"]
            first_before = summary["before"]["first_grade"]
            first_after = summary["after"]["first_grade"]
            moved = summary["to_move"]

            print(
                f"{year_id:>11} | {k_before:>2} → {k_after:<2}         | {first_before:>3} → {first_after:<3}         | {moved:>13}"
            )

        print(f"\n✅ {csv_file_path} has been successfully modified!")
        print(
            "⚠️  Remember to update your grade_levels table to include grade_level_id = 0 for Kindergarten"
        )

    except FileNotFoundError:
        print(f"❌ Error: Could not find {csv_file_path}")
        print("   Make sure the file exists in the current directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during redistribution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Default path for your folder structure: scripts/ folder running on ../data/clean_csv/ files
    redistribute_grade_levels("../data/clean_csv/students.csv")
