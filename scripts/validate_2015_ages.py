#!/usr/bin/env python3
# flake8: noqa
"""
Validate student ages relative to 2015-2016 school year

This script recalculates student ages using the correct baseline year
and validates age-grade alignment for the 2015-2016 school year.
"""

import logging
from datetime import date, datetime

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def validate_ages_2015():
    """Validate student ages for 2015-2016 school year"""

    # Load students and grade levels (from scripts folder, go up one level)
    students_df = pd.read_csv("../data/clean_csv/students.csv")
    grade_levels_df = pd.read_csv("../data/clean_csv/grade_levels.csv")

    logger.info(f"Loaded {len(students_df)} students")

    # Calculate ages relative to 2015-2016 school year (use Sept 1, 2015)
    reference_date = date(2015, 9, 1)
    students_df["date_of_birth"] = pd.to_datetime(students_df["date_of_birth"])
    students_df["age_2015"] = (
        pd.Timestamp(reference_date) - students_df["date_of_birth"]
    ).dt.days / 365.25

    # Expected age ranges by grade level for 2015-2016
    grade_age_expectations = {
        1: (5, 6),  # Kindergarten
        2: (6, 7),  # 1st Grade
        3: (7, 8),  # 2nd Grade
        4: (8, 9),  # 3rd Grade
        5: (9, 10),  # 4th Grade
        6: (10, 11),  # 5th Grade
        7: (11, 12),  # 6th Grade
        8: (12, 13),  # 7th Grade
        9: (13, 14),  # 8th Grade
        10: (14, 15),  # 9th Grade
        11: (15, 16),  # 10th Grade
        12: (16, 17),  # 11th Grade
        13: (17, 18),  # 12th Grade
    }

    # Validate age-grade alignment
    mismatches = 0
    grade_age_summary = {}

    for grade_id in range(1, 14):
        grade_students = students_df[students_df["grade_level_id"] == grade_id]
        if len(grade_students) == 0:
            continue

        min_expected, max_expected = grade_age_expectations[grade_id]
        actual_ages = grade_students["age_2015"]

        # Allow 1-year buffer on each side (kids can be held back or skip)
        valid_ages = actual_ages[
            (actual_ages >= min_expected - 1) & (actual_ages <= max_expected + 1)
        ]
        invalid_count = len(grade_students) - len(valid_ages)

        grade_label = grade_levels_df[grade_levels_df["grade_level_id"] == grade_id][
            "label"
        ].iloc[0]

        grade_age_summary[grade_label] = {
            "count": len(grade_students),
            "mean_age": round(actual_ages.mean(), 1),
            "min_age": round(actual_ages.min(), 1),
            "max_age": round(actual_ages.max(), 1),
            "expected_range": f"{min_expected}-{max_expected}",
            "invalid_count": invalid_count,
        }

        mismatches += invalid_count

    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("AGE-GRADE VALIDATION FOR 2015-2016 SCHOOL YEAR")
    logger.info("=" * 60)

    print(
        f"{'Grade':<12} {'Count':<6} {'Mean Age':<9} {'Age Range':<12} {'Expected':<10} {'Issues':<6}"
    )
    print("-" * 65)

    total_issues = 0
    for grade_label, data in grade_age_summary.items():
        issues = data["invalid_count"]
        total_issues += issues
        issue_marker = "❌" if issues > 0 else "✅"

        print(
            f"{grade_label:<12} {data['count']:<6} {data['mean_age']:<9} "
            f"{data['min_age']:.1f}-{data['max_age']:.1f} {' ':<3} {data['expected_range']:<10} "
            f"{issues:<6} {issue_marker}"
        )

    print("\n" + "=" * 60)

    if total_issues == 0:
        logger.info("✅ ALL AGES ARE VALID FOR 2015-2016 SCHOOL YEAR!")
        logger.info("Data is ready for decade expansion!")
    else:
        logger.warning(f"❌ Found {total_issues} age-grade mismatches")
        logger.info("These may need correction before decade expansion")

    # Show some sample birth dates for verification
    logger.info(f"\nSample birth dates for verification:")
    for grade_id in [1, 7, 13]:  # K, 6th, 12th grade samples
        grade_students = students_df[students_df["grade_level_id"] == grade_id].head(3)
        grade_label = grade_levels_df[grade_levels_df["grade_level_id"] == grade_id][
            "label"
        ].iloc[0]

        print(f"\n{grade_label} samples:")
        for _, student in grade_students.iterrows():
            birth_date = student["date_of_birth"].strftime("%Y-%m-%d")
            age_2015 = student["age_2015"]
            print(f"  Born: {birth_date} → Age in 2015: {age_2015:.1f}")

    return total_issues == 0


if __name__ == "__main__":
    is_valid = validate_ages_2015()
    if is_valid:
        print(f"\n🎯 Data validation PASSED! Ready for decade expansion.")
        exit(0)
    else:
        print(f"\n⚠️  Data validation FAILED. Issues need to be addressed.")
        exit(1)
