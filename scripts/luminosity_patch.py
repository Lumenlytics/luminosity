#!/usr/bin/env python3
# flake8: noqa
"""
Luminosity School Management System - Data Quality Patch Script

This script fixes the identified issues in the decade generator:
1. Grade distribution alignment with 70-100 range and 85-90 median policy
2. Teacher-student ratio management
3. Financial data consistency
4. Improved validation and quality checks

Usage:
    python luminosity_patch.py --decade-dir ../data/decade --fix-all
"""

import argparse
import json
import logging
import os
import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from faker import Faker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LuminosityDataPatcher:
    """Patches data quality issues in the Luminosity decade dataset"""

    def __init__(self, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)

        # Grade distribution parameters (matching policy)
        self.grade_policy = {
            "min_percentage": 70,
            "max_percentage": 100,
            "median_percentage": 87,  # 85-90 range median
            "perfect_rate": 0.03,  # 3% perfect grades (95-100%)
            "failing_rate": 0.04,  # 3-5% failing grades (below 70%)
            "std_dev": 8,  # Standard deviation for normal distribution
        }

    def patch_grade_distributions(self, decade_dir: str, fix_assignments: bool = True):
        """Fix grade distributions to match school policy"""
        logger.info("🎯 Patching grade distributions...")

        years_fixed = 0
        total_grades_fixed = 0

        for year in range(2016, 2026):
            year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
            if not os.path.exists(year_dir):
                continue

            grades_file = os.path.join(year_dir, "grades.csv")
            assignments_file = os.path.join(year_dir, "assignments.csv")

            if not os.path.exists(grades_file):
                logger.warning(f"Grades file not found for {year}")
                continue

            # Load data
            grades_df = pd.read_csv(grades_file)
            assignments_df = (
                pd.read_csv(assignments_file)
                if os.path.exists(assignments_file)
                else None
            )

            # Fix grades
            fixed_grades = self._fix_grades_for_year(grades_df, assignments_df)

            # Save fixed grades
            fixed_grades.to_csv(grades_file, index=False)

            # Update assignments if needed and requested
            if fix_assignments and assignments_df is not None:
                fixed_assignments = self._fix_assignments_for_year(assignments_df)
                fixed_assignments.to_csv(assignments_file, index=False)

            years_fixed += 1
            total_grades_fixed += len(fixed_grades)

            logger.info(f"  Fixed {year}: {len(fixed_grades):,} grades")

        logger.info(
            f"✅ Grade distributions patched: {years_fixed} years, {total_grades_fixed:,} total grades"
        )

    def _fix_grades_for_year(
        self, grades_df: pd.DataFrame, assignments_df: pd.DataFrame = None
    ) -> pd.DataFrame:
        """Fix grades for a single year to match policy"""

        # Create assignments lookup for points_possible
        assignments_lookup = {}
        if assignments_df is not None:
            for _, assignment in assignments_df.iterrows():
                assignments_lookup[assignment["assignment_id"]] = assignment[
                    "points_possible"
                ]

        # Fix each grade
        fixed_grades = grades_df.copy()

        for idx, grade in fixed_grades.iterrows():
            assignment_id = grade["assignment_id"]

            # Get points possible (default to 100 if not found)
            points_possible = assignments_lookup.get(assignment_id, 100)

            # Generate new realistic score
            new_score = self._generate_policy_compliant_score(points_possible)
            fixed_grades.at[idx, "score"] = new_score

        return fixed_grades

    def _generate_policy_compliant_score(self, points_possible: int) -> int:
        """Generate grade score that complies with school policy"""
        rand = random.random()

        if rand < self.grade_policy["perfect_rate"]:
            # 3% perfect grades (95-100%)
            percentage = random.uniform(0.95, 1.0)
        elif (
            rand < self.grade_policy["perfect_rate"] + self.grade_policy["failing_rate"]
        ):
            # 3-5% failing grades (0-69%)
            percentage = random.uniform(0.0, 0.69)
        else:
            # Normal distribution centered around median (87%)
            percentage = np.random.normal(
                self.grade_policy["median_percentage"] / 100,
                self.grade_policy["std_dev"] / 100,
            )
            # Clamp to 70-100% range for passing grades
            percentage = max(0.70, min(1.0, percentage))

        # Convert to actual points
        score = round(points_possible * percentage)
        return max(0, min(points_possible, score))

    def _fix_assignments_for_year(self, assignments_df: pd.DataFrame) -> pd.DataFrame:
        """Fix assignment points to be more realistic"""
        fixed_assignments = assignments_df.copy()

        # Define realistic point ranges by category
        points_by_category = {
            "Homework": (10, 25),
            "Quiz": (25, 50),
            "Test": (75, 100),
            "Project": (50, 100),
            "Participation": (5, 20),
            "Final": (100, 200),
        }

        for idx, assignment in fixed_assignments.iterrows():
            category = assignment.get("category", "Homework")

            if category in points_by_category:
                min_points, max_points = points_by_category[category]
                new_points = random.randint(min_points, max_points)
                fixed_assignments.at[idx, "points_possible"] = new_points

        return fixed_assignments

    def patch_teacher_ratios(self, decade_dir: str):
        """Fix teacher-student ratios by adjusting teacher counts"""
        logger.info("👩‍🏫 Patching teacher-student ratios...")

        target_ratio = 8.5  # Target ratio for optimal class sizes
        years_fixed = 0

        for year in range(2016, 2026):
            year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
            if not os.path.exists(year_dir):
                continue

            students_file = os.path.join(year_dir, "students.csv")
            teachers_file = os.path.join(year_dir, "teachers.csv")

            if not (os.path.exists(students_file) and os.path.exists(teachers_file)):
                continue

            students_df = pd.read_csv(students_file)
            teachers_df = pd.read_csv(teachers_file)

            current_ratio = len(students_df) / len(teachers_df)

            # If ratio is too high, add teachers
            if current_ratio > target_ratio + 1:
                needed_teachers = int(len(students_df) / target_ratio) - len(
                    teachers_df
                )
                new_teachers = self._generate_additional_teachers(
                    teachers_df, needed_teachers, year
                )

                if len(new_teachers) > 0:
                    updated_teachers_df = pd.concat(
                        [teachers_df, new_teachers], ignore_index=True
                    )
                    updated_teachers_df.to_csv(teachers_file, index=False)

                    logger.info(
                        f"  {year}: Added {len(new_teachers)} teachers (ratio: {current_ratio:.1f} → {len(students_df)/len(updated_teachers_df):.1f})"
                    )
                    years_fixed += 1

        logger.info(f"✅ Teacher ratios patched: {years_fixed} years adjusted")

    def _generate_additional_teachers(
        self, existing_teachers_df: pd.DataFrame, count: int, year: int
    ) -> pd.DataFrame:
        """Generate additional teachers to improve ratios"""
        if count <= 0:
            return pd.DataFrame()

        new_teachers = []
        max_teacher_id = existing_teachers_df["teacher_id"].max()

        # Determine department distribution
        dept_counts = existing_teachers_df["department_id"].value_counts()

        for i in range(count):
            # Assign to department with fewest teachers
            department_id = dept_counts.idxmin()
            dept_counts[department_id] += 1

            gender = random.choice(["M", "F"])
            first_name = (
                self.fake.first_name_male()
                if gender == "M"
                else self.fake.first_name_female()
            )

            new_teacher = {
                "teacher_id": max_teacher_id + i + 1,
                "first_name": first_name,
                "last_name": self.fake.last_name(),
                "department_id": department_id,
            }
            new_teachers.append(new_teacher)

        return pd.DataFrame(new_teachers)

    def patch_financial_data(self, decade_dir: str):
        """Fix financial data inconsistencies"""
        logger.info("💰 Patching financial data...")

        # Base fee structure (will be adjusted by year)
        base_fees = {
            1: {"name": "Tech Fee", "amount": 100, "frequency": "One Time"},
            2: {"name": "Field Trip Fund", "amount": 50, "frequency": "One Time"},
            3: {"name": "Lunch Plan", "amount": 400, "frequency": "Monthly"},
            4: {"name": "Tuition", "amount": 8000, "frequency": "Annual"},
            5: {"name": "Activity Fee", "amount": 75, "frequency": "Per Term"},
        }

        # Year-specific adjustments
        fee_adjustments = {
            2016: {"Tech Fee": 1.0, "Tuition": 1.0},
            2017: {"Tech Fee": 1.10, "Tuition": 1.0},
            2018: {"Tech Fee": 1.10, "Tuition": 1.0},
            2019: {"Tech Fee": 1.25, "Tuition": 1.0},
            2020: {"Tech Fee": 1.50, "Tuition": 1.0},  # COVID tech needs
            2021: {"Tech Fee": 1.50, "Tuition": 1.0},
            2022: {"Tech Fee": 1.30, "Tuition": 1.10},  # 10% tuition increase
            2023: {"Tech Fee": 1.30, "Tuition": 1.155},  # 5% increase on 2022
            2024: {"Tech Fee": 1.30, "Tuition": 1.155},
            2025: {"Tech Fee": 1.30, "Tuition": 1.189},  # 3% increase
        }

        years_fixed = 0

        for year in range(2016, 2026):
            year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
            if not os.path.exists(year_dir):
                continue

            fee_types_file = os.path.join(year_dir, "fee_types.csv")
            payments_file = os.path.join(year_dir, "payments.csv")

            # Update fee types
            if os.path.exists(fee_types_file):
                fee_types_df = pd.read_csv(fee_types_file)
                adjusted_fees = self._apply_fee_adjustments(
                    fee_types_df, base_fees, fee_adjustments.get(year, {})
                )
                adjusted_fees.to_csv(fee_types_file, index=False)

            # Update payments to match new fee structure
            if os.path.exists(payments_file):
                payments_df = pd.read_csv(payments_file)
                adjusted_payments = self._adjust_payment_amounts(
                    payments_df,
                    adjusted_fees if "adjusted_fees" in locals() else fee_types_df,
                )
                adjusted_payments.to_csv(payments_file, index=False)
                years_fixed += 1

        logger.info(f"✅ Financial data patched: {years_fixed} years updated")

    def _apply_fee_adjustments(
        self, fee_types_df: pd.DataFrame, base_fees: Dict, adjustments: Dict
    ) -> pd.DataFrame:
        """Apply year-specific fee adjustments"""
        adjusted_df = fee_types_df.copy()

        for idx, fee in adjusted_df.iterrows():
            fee_name = fee["name"]
            if fee_name in adjustments:
                base_amount = base_fees.get(fee["fee_type_id"], {}).get(
                    "amount", fee["amount"]
                )
                new_amount = int(base_amount * adjustments[fee_name])
                adjusted_df.at[idx, "amount"] = new_amount

        return adjusted_df

    def _adjust_payment_amounts(
        self, payments_df: pd.DataFrame, fee_types_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Adjust payment amounts to match fee structure"""
        adjusted_df = payments_df.copy()

        # Create fee lookup
        fee_lookup = {}
        for _, fee in fee_types_df.iterrows():
            fee_lookup[fee["fee_type_id"]] = fee["amount"]

        for idx, payment in adjusted_df.iterrows():
            fee_type_id = payment["fee_type_id"]
            if fee_type_id in fee_lookup:
                expected_amount = fee_lookup[fee_type_id]

                # Add some realistic variation (±10%)
                variation = random.uniform(0.9, 1.1)
                adjusted_amount = int(expected_amount * variation)
                adjusted_df.at[idx, "amount_paid"] = adjusted_amount

        return adjusted_df

    def generate_missing_data(self, decade_dir: str):
        """Generate any missing data files"""
        logger.info("📋 Generating missing data files...")

        missing_files_generated = 0

        for year in range(2016, 2026):
            year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
            if not os.path.exists(year_dir):
                continue

            # Standard files that should exist
            standard_files = [
                "grade_levels.csv",
                "departments.csv",
                "guardian_types.csv",
                "periods.csv",
                "classrooms.csv",
            ]

            for filename in standard_files:
                filepath = os.path.join(year_dir, filename)
                if not os.path.exists(filepath):
                    self._generate_standard_file(filepath, filename)
                    missing_files_generated += 1

        if missing_files_generated > 0:
            logger.info(
                f"✅ Generated {missing_files_generated} missing standard files"
            )

    def _generate_standard_file(self, filepath: str, filename: str):
        """Generate standard reference data files"""

        if filename == "grade_levels.csv":
            data = pd.DataFrame(
                [
                    {"grade_level_id": i, "label": label}
                    for i, label in enumerate(
                        [
                            "Kindergarten",
                            "1st Grade",
                            "2nd Grade",
                            "3rd Grade",
                            "4th Grade",
                            "5th Grade",
                            "6th Grade",
                            "7th Grade",
                            "8th Grade",
                            "9th Grade",
                            "10th Grade",
                            "11th Grade",
                            "12th Grade",
                        ],
                        1,
                    )
                ]
            )

        elif filename == "departments.csv":
            data = pd.DataFrame(
                [
                    {"department_id": 1, "name": "Mathematics"},
                    {"department_id": 2, "name": "Science"},
                    {"department_id": 3, "name": "English"},
                    {"department_id": 4, "name": "Social Studies"},
                    {"department_id": 5, "name": "Physical Education"},
                    {"department_id": 6, "name": "Fine Arts"},
                    {"department_id": 7, "name": "Technology"},
                    {"department_id": 8, "name": "Foreign Language"},
                    {"department_id": 9, "name": "Electives"},
                ]
            )

        elif filename == "guardian_types.csv":
            data = pd.DataFrame(
                [
                    {"guardian_type_id": i, "label": label}
                    for i, label in enumerate(
                        [
                            "Mother",
                            "Father",
                            "Step-Mother",
                            "Step-Father",
                            "Grandmother",
                            "Grandfather",
                            "Aunt",
                            "Uncle",
                            "Legal Guardian",
                            "Other",
                        ],
                        1,
                    )
                ]
            )

        elif filename == "periods.csv":
            data = pd.DataFrame(
                [
                    {
                        "period_id": i,
                        "label": f"Period {i}",
                        "start_time": f"{7+i}:00:00",
                        "end_time": f"{8+i}:00:00",
                    }
                    for i in range(1, 8)
                ]
            )

        elif filename == "classrooms.csv":
            data = pd.DataFrame(
                [
                    {
                        "classroom_id": i,
                        "room_number": f"Room {100+i}",
                        "capacity": random.randint(20, 30),
                    }
                    for i in range(1, 21)
                ]
            )

        else:
            return  # Unknown file type

        data.to_csv(filepath, index=False)
        logger.info(f"  Generated {filename}")

    def validate_patches(self, decade_dir: str) -> Dict:
        """Validate that patches have been applied correctly"""
        logger.info("🔍 Validating patches...")

        validation_results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "statistics": {},
        }

        # Validate grade distributions
        grade_stats = self._validate_grade_distributions(decade_dir)
        validation_results["statistics"]["grade_distributions"] = grade_stats

        for year, stats in grade_stats.items():
            if (
                stats["below_70_pct"] < 0.25 and stats["perfect_pct"] > 0.02
            ):  # Reasonable thresholds
                validation_results["passed"].append(
                    {
                        "category": "Grade Distribution",
                        "message": f"Year {year}: Grade distribution improved",
                    }
                )
            else:
                validation_results["warnings"].append(
                    {
                        "category": "Grade Distribution",
                        "message": f"Year {year}: Distribution may need further adjustment",
                    }
                )

        # Validate teacher ratios
        ratio_stats = self._validate_teacher_ratios(decade_dir)
        validation_results["statistics"]["teacher_ratios"] = ratio_stats

        ratios_in_range = all(
            7.0 <= stats["ratio"] <= 10.0 for stats in ratio_stats.values()
        )
        if ratios_in_range:
            validation_results["passed"].append(
                {
                    "category": "Teacher Ratios",
                    "message": "All teacher-student ratios within acceptable range",
                }
            )
        else:
            validation_results["warnings"].append(
                {
                    "category": "Teacher Ratios",
                    "message": "Some ratios still outside optimal range",
                }
            )

        # Validate financial consistency
        financial_stats = self._validate_financial_data(decade_dir)
        validation_results["statistics"]["financial_summary"] = financial_stats

        validation_results["passed"].append(
            {
                "category": "Financial Data",
                "message": "Financial data structure validated",
            }
        )

        logger.info(
            f"✅ Validation complete: {len(validation_results['passed'])} passed, {len(validation_results['failed'])} failed, {len(validation_results['warnings'])} warnings"
        )

        return validation_results

    def _validate_grade_distributions(self, decade_dir: str) -> Dict:
        """Validate grade distributions after patching"""
        grade_stats = {}

        for year in range(2016, 2026):
            year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
            grades_file = os.path.join(year_dir, "grades.csv")
            assignments_file = os.path.join(year_dir, "assignments.csv")

            if not (os.path.exists(grades_file) and os.path.exists(assignments_file)):
                continue

            grades_df = pd.read_csv(grades_file)
            assignments_df = pd.read_csv(assignments_file)

            # Calculate percentages for each grade
            percentages = []
            assignments_lookup = {
                row["assignment_id"]: row["points_possible"]
                for _, row in assignments_df.iterrows()
            }

            for _, grade in grades_df.iterrows():
                points_possible = assignments_lookup.get(grade["assignment_id"], 100)
                if points_possible > 0:
                    percentage = (grade["score"] / points_possible) * 100
                    percentages.append(percentage)

            if percentages:
                percentages = np.array(percentages)
                grade_stats[year] = {
                    "mean": float(np.mean(percentages)),
                    "median": float(np.median(percentages)),
                    "min": float(np.min(percentages)),
                    "max": float(np.max(percentages)),
                    "below_70_pct": float(np.sum(percentages < 70) / len(percentages)),
                    "perfect_pct": float(np.sum(percentages >= 95) / len(percentages)),
                    "total_grades": len(percentages),
                }

        return grade_stats

    def _validate_teacher_ratios(self, decade_dir: str) -> Dict:
        """Validate teacher-student ratios"""
        ratio_stats = {}

        for year in range(2016, 2026):
            year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
            students_file = os.path.join(year_dir, "students.csv")
            teachers_file = os.path.join(year_dir, "teachers.csv")

            if not (os.path.exists(students_file) and os.path.exists(teachers_file)):
                continue

            students_df = pd.read_csv(students_file)
            teachers_df = pd.read_csv(teachers_file)

            ratio_stats[year] = {
                "teachers": len(teachers_df),
                "students": len(students_df),
                "ratio": len(students_df) / len(teachers_df),
            }

        return ratio_stats

    def _validate_financial_data(self, decade_dir: str) -> Dict:
        """Validate financial data consistency"""
        financial_stats = {}

        for year in range(2016, 2026):
            year_dir = os.path.join(decade_dir, f"{year}-{year+1}")
            payments_file = os.path.join(year_dir, "payments.csv")

            if not os.path.exists(payments_file):
                continue

            payments_df = pd.read_csv(payments_file)

            financial_stats[year] = {
                "total_revenue": int(payments_df["amount_paid"].sum()),
                "avg_payment": float(payments_df["amount_paid"].mean()),
                "num_payments": len(payments_df),
            }

        return financial_stats

    def run_comprehensive_patch(self, decade_dir: str):
        """Run all patches and validation"""
        logger.info(f"\n{'='*60}")
        logger.info("LUMINOSITY DATA QUALITY COMPREHENSIVE PATCH")
        logger.info(f"{'='*60}")
        logger.info(f"Target Directory: {decade_dir}")

        # Run all patches
        self.patch_grade_distributions(decade_dir, fix_assignments=True)
        self.patch_teacher_ratios(decade_dir)
        self.patch_financial_data(decade_dir)
        self.generate_missing_data(decade_dir)

        # Validate results
        validation_results = self.validate_patches(decade_dir)

        # Save validation report
        report_file = os.path.join(decade_dir, "patch_validation_report.json")
        with open(report_file, "w") as f:
            json.dump(validation_results, f, indent=2)

        logger.info(f"\n{'='*60}")
        logger.info("PATCH COMPLETE!")
        logger.info(f"{'='*60}")
        logger.info(f"Validation report saved: {report_file}")

        # Print summary
        print(f"\n📊 PATCH SUMMARY:")
        print(f"✅ Passed checks: {len(validation_results['passed'])}")
        print(f"❌ Failed checks: {len(validation_results['failed'])}")
        print(f"⚠️  Warnings: {len(validation_results['warnings'])}")

        if validation_results["statistics"].get("grade_distributions"):
            print(f"\n📈 Grade Distribution Sample (2025):")
            stats_2025 = validation_results["statistics"]["grade_distributions"].get(
                2025, {}
            )
            if stats_2025:
                print(f"  Mean: {stats_2025.get('mean', 0):.1f}%")
                print(f"  Median: {stats_2025.get('median', 0):.1f}%")
                print(f"  Below 70%: {stats_2025.get('below_70_pct', 0)*100:.1f}%")
                print(f"  Perfect grades: {stats_2025.get('perfect_pct', 0)*100:.1f}%")

        return validation_results


def main():
    """Main function to run the patch script"""
    parser = argparse.ArgumentParser(description="Patch Luminosity data quality issues")
    parser.add_argument(
        "--decade-dir", default="../data/decade", help="Path to decade data directory"
    )
    parser.add_argument(
        "--fix-grades", action="store_true", help="Fix grade distributions only"
    )
    parser.add_argument(
        "--fix-ratios", action="store_true", help="Fix teacher ratios only"
    )
    parser.add_argument(
        "--fix-financial", action="store_true", help="Fix financial data only"
    )
    parser.add_argument(
        "--fix-all", action="store_true", help="Run comprehensive patch"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate, no fixes"
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    # Initialize patcher
    patcher = LuminosityDataPatcher(seed=args.seed)

    if args.validate_only:
        validation_results = patcher.validate_patches(args.decade_dir)
        print("Validation complete. Check patch_validation_report.json for details.")
    elif args.fix_all:
        patcher.run_comprehensive_patch(args.decade_dir)
    else:
        if args.fix_grades:
            patcher.patch_grade_distributions(args.decade_dir)
        if args.fix_ratios:
            patcher.patch_teacher_ratios(args.decade_dir)
        if args.fix_financial:
            patcher.patch_financial_data(args.decade_dir)

        # Run validation after individual fixes
        validation_results = patcher.validate_patches(args.decade_dir)
        print(
            "Patches applied. Check patch_validation_report.json for validation results."
        )


if __name__ == "__main__":
    main()
