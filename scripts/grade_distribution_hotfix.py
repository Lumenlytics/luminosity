#!/usr/bin/env python3
# flake8: noqa
"""
Definitive fix for Luminosity grade distribution issues

This script identifies and fixes the core disconnect between grade generation
and validation interpretation.
"""

import logging
import os
import random

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def analyze_current_grade_issue(decade_dir: str):
    """Analyze what's actually happening with grades"""

    print("🔍 ANALYZING CURRENT GRADE ISSUE...")

    # Check one year in detail
    year = 2025
    year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
    grades_file = os.path.join(year_dir, "grades.csv")
    assignments_file = os.path.join(year_dir, "assignments.csv")

    if not (os.path.exists(grades_file) and os.path.exists(assignments_file)):
        print(f"❌ Cannot find files for {year}")
        return

    grades_df = pd.read_csv(grades_file)
    assignments_df = pd.read_csv(assignments_file)

    # Sample analysis
    sample_size = min(1000, len(grades_df))
    sample_grades = grades_df.sample(sample_size)

    print(f"\n📊 SAMPLE ANALYSIS ({sample_size} grades from {year}):")

    # Create assignment lookup
    assignment_lookup = {
        row["assignment_id"]: row["points_possible"]
        for _, row in assignments_df.iterrows()
    }

    percentages = []
    raw_scores = []
    points_possible_list = []

    for _, grade in sample_grades.iterrows():
        assignment_id = grade["assignment_id"]
        score = grade["score"]
        points_possible = assignment_lookup.get(assignment_id, 100)

        percentage = (score / points_possible) * 100 if points_possible > 0 else 0

        percentages.append(percentage)
        raw_scores.append(score)
        points_possible_list.append(points_possible)

    percentages = np.array(percentages)
    raw_scores = np.array(raw_scores)
    points_possible_list = np.array(points_possible_list)

    print(
        f"Raw Scores - Mean: {np.mean(raw_scores):.1f}, Median: {np.median(raw_scores):.1f}"
    )
    print(
        f"Percentages - Mean: {np.mean(percentages):.1f}%, Median: {np.median(percentages):.1f}%"
    )
    print(
        f"Points Possible - Min: {np.min(points_possible_list)}, Max: {np.max(points_possible_list)}, Mean: {np.mean(points_possible_list):.1f}"
    )

    print(f"\nPercentage Distribution:")
    print(f"  Below 70%: {np.sum(percentages < 70) / len(percentages) * 100:.1f}%")
    print(
        f"  70-89%: {np.sum((percentages >= 70) & (percentages < 90)) / len(percentages) * 100:.1f}%"
    )
    print(
        f"  90-94%: {np.sum((percentages >= 90) & (percentages < 95)) / len(percentages) * 100:.1f}%"
    )
    print(f"  95-100%: {np.sum(percentages >= 95) / len(percentages) * 100:.1f}%")

    # Check assignment distribution
    assignment_points = assignments_df["points_possible"].values
    print(f"\nAssignment Points Distribution:")
    print(f"  Min: {np.min(assignment_points)}, Max: {np.max(assignment_points)}")
    print(
        f"  Mean: {np.mean(assignment_points):.1f}, Median: {np.median(assignment_points):.1f}"
    )

    return {
        "raw_mean": np.mean(raw_scores),
        "percentage_mean": np.mean(percentages),
        "below_70_pct": np.sum(percentages < 70) / len(percentages),
        "perfect_pct": np.sum(percentages >= 95) / len(percentages),
    }


def generate_proper_grades(decade_dir: str):
    """Generate grades with proper policy-compliant distribution"""

    print("\n🎯 GENERATING PROPER GRADES...")

    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)

    total_grades_fixed = 0

    for year in range(2016, 2026):
        year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
        if not os.path.exists(year_dir):
            continue

        grades_file = os.path.join(year_dir, "grades.csv")
        assignments_file = os.path.join(year_dir, "assignments.csv")

        if not (os.path.exists(grades_file) and os.path.exists(assignments_file)):
            continue

        grades_df = pd.read_csv(grades_file)
        assignments_df = pd.read_csv(assignments_file)

        # Create assignment lookup
        assignment_lookup = {
            row["assignment_id"]: row["points_possible"]
            for _, row in assignments_df.iterrows()
        }

        # Generate new grades with correct distribution
        new_grades = []

        for _, grade in grades_df.iterrows():
            assignment_id = grade["assignment_id"]
            points_possible = assignment_lookup.get(assignment_id, 100)

            # Generate percentage first using CORRECT distribution
            rand = random.random()

            if rand < 0.03:  # 3% perfect grades (95-100%)
                percentage = random.uniform(95, 100)
            elif rand < 0.08:  # 5% failing grades (below 70%)
                percentage = random.uniform(0, 69)
            else:  # 92% normal grades
                # Normal distribution centered at 85% (middle of 85-90 range)
                percentage = np.random.normal(85, 5)  # 5-point std dev
                # Clamp to reasonable range for passing grades
                percentage = max(70, min(94, percentage))

            # Convert percentage to points
            score = round((percentage / 100) * points_possible)
            score = max(0, min(points_possible, score))

            new_grades.append(
                {
                    "grade_id": grade["grade_id"],
                    "student_id": grade["student_id"],
                    "assignment_id": grade["assignment_id"],
                    "score": score,
                    "submitted_on": grade["submitted_on"],
                    "term_id": grade.get(
                        " term_id", grade.get("term_id", 1)
                    ),  # Handle space issue
                }
            )

        # Save new grades
        new_grades_df = pd.DataFrame(new_grades)
        new_grades_df.to_csv(grades_file, index=False)

        total_grades_fixed += len(new_grades)
        print(f"  ✅ {year}: Fixed {len(new_grades):,} grades")

    print(f"\n✅ GRADE GENERATION COMPLETE: {total_grades_fixed:,} total grades fixed")


def validate_grade_fix(decade_dir: str):
    """Validate that the grade fix worked correctly"""

    print("\n🔍 VALIDATING GRADE FIX...")

    validation_summary = {}

    for year in range(2016, 2026):
        year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
        if not os.path.exists(year_dir):
            continue

        grades_file = os.path.join(year_dir, "grades.csv")
        assignments_file = os.path.join(year_dir, "assignments.csv")

        if not (os.path.exists(grades_file) and os.path.exists(assignments_file)):
            continue

        grades_df = pd.read_csv(grades_file)
        assignments_df = pd.read_csv(assignments_file)

        # Calculate percentages
        assignment_lookup = {
            row["assignment_id"]: row["points_possible"]
            for _, row in assignments_df.iterrows()
        }

        percentages = []
        for _, grade in grades_df.iterrows():
            points_possible = assignment_lookup.get(grade["assignment_id"], 100)
            if points_possible > 0:
                percentage = (grade["score"] / points_possible) * 100
                percentages.append(percentage)

        if percentages:
            percentages = np.array(percentages)

            validation_summary[year] = {
                "mean_percentage": float(np.mean(percentages)),
                "median_percentage": float(np.median(percentages)),
                "below_70_pct": float(np.sum(percentages < 70) / len(percentages)),
                "perfect_pct": float(np.sum(percentages >= 95) / len(percentages)),
                "passing_pct": float(np.sum(percentages >= 70) / len(percentages)),
                "total_grades": len(percentages),
            }

    # Print summary
    if validation_summary:
        sample_year = 2025
        if sample_year in validation_summary:
            stats = validation_summary[sample_year]
            print(f"\n📊 VALIDATION RESULTS (Sample: {sample_year}):")
            print(f"  Mean Percentage: {stats['mean_percentage']:.1f}%")
            print(f"  Median Percentage: {stats['median_percentage']:.1f}%")
            print(f"  Below 70% (Failing): {stats['below_70_pct']*100:.1f}%")
            print(f"  Above 95% (Perfect): {stats['perfect_pct']*100:.1f}%")
            print(f"  Passing Rate: {stats['passing_pct']*100:.1f}%")
            print(f"  Total Grades: {stats['total_grades']:,}")

            # Check if it meets policy
            meets_policy = (
                80 <= stats["mean_percentage"] <= 90
                and stats["below_70_pct"] < 0.10  # Less than 10% failing
                and 0.02 <= stats["perfect_pct"] <= 0.05  # 2-5% perfect
            )

            if meets_policy:
                print(f"\n✅ POLICY COMPLIANCE: PASSED")
            else:
                print(f"\n❌ POLICY COMPLIANCE: NEEDS ADJUSTMENT")

        print(f"\n📈 DECADE TREND:")
        for year in sorted(validation_summary.keys()):
            stats = validation_summary[year]
            print(
                f"  {year}: {stats['mean_percentage']:.1f}% avg, {stats['below_70_pct']*100:.1f}% failing, {stats['perfect_pct']*100:.1f}% perfect"
            )

    return validation_summary


def main():
    """Run complete grade distribution analysis and fix"""

    decade_dir = "../data/decade"

    print("🏫 LUMINOSITY GRADE DISTRIBUTION - DEFINITIVE FIX")
    print("=" * 60)

    # Step 1: Analyze current issue
    current_stats = analyze_current_grade_issue(decade_dir)

    # Step 2: Generate proper grades
    generate_proper_grades(decade_dir)

    # Step 3: Validate the fix
    validation_results = validate_grade_fix(decade_dir)

    print("\n" + "=" * 60)
    print("🎓 GRADE DISTRIBUTION FIX COMPLETE!")
    print("=" * 60)

    if validation_results:
        print("Expected results:")
        print("  ✅ Mean grades: 80-90%")
        print("  ✅ Failing rate: <10%")
        print("  ✅ Perfect rate: 2-5%")
        print("  ✅ Policy compliant distribution")


if __name__ == "__main__":
    main()
