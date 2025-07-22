#!/usr/bin/env python3
# flake8: noqa
"""
Luminosity Decade Data Validator

This script validates the generated 10-year dataset to ensure:
- Data quality and consistency
- Business rule compliance
- Referential integrity
- Realistic distributions
- Longitudinal coherence

Usage:
    python validate_decade_data.py --data-dir ../data/decade
"""

import argparse
import json
import logging
import os
import warnings
from collections import defaultdict
from datetime import date, datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LuminosityDataValidator:
    """Comprehensive validator for Luminosity decade data"""

    def __init__(self, data_directory):
        self.data_dir = data_directory
        self.years = []
        self.yearly_data = {}
        self.validation_results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "statistics": {},
        }

    def load_decade_data(self):
        """Load all year data into memory"""
        logger.info("Loading decade data...")

        # Find all year directories
        for item in os.listdir(self.data_dir):
            if "-" in item and os.path.isdir(os.path.join(self.data_dir, item)):
                year = int(item.split("-")[0])
                self.years.append(year)

        self.years.sort()
        logger.info(f"Found {len(self.years)} years: {self.years}")

        # Load data for each year
        for year in self.years:
            year_dir = os.path.join(self.data_dir, f"{year}-{year+1}")
            self.yearly_data[year] = self._load_year_data(year_dir)

        logger.info("All data loaded successfully")

    def _load_year_data(self, year_dir):
        """Load all CSV files for a specific year"""
        year_data = {}

        csv_files = [f for f in os.listdir(year_dir) if f.endswith(".csv")]
        for csv_file in csv_files:
            table_name = csv_file.replace(".csv", "")
            filepath = os.path.join(year_dir, csv_file)
            try:
                year_data[table_name] = pd.read_csv(filepath)
            except Exception as e:
                logger.warning(f"Could not load {csv_file}: {e}")

        return year_data

    def validate_all(self):
        """Run all validation checks"""
        logger.info("🔍 STARTING COMPREHENSIVE VALIDATION")
        logger.info("=" * 60)

        # Core data integrity
        self._validate_file_structure()
        self._validate_referential_integrity()
        self._validate_data_types()

        # Business rule compliance
        self._validate_enrollment_progression()
        self._validate_attendance_policies()
        self._validate_grade_distributions()
        self._validate_teacher_assignments()
        self._validate_financial_data()

        # Longitudinal consistency
        self._validate_student_progression()
        self._validate_teacher_continuity()
        self._validate_curriculum_evolution()

        # Statistical realism
        self._validate_demographic_distributions()
        self._validate_academic_performance()
        self._validate_operational_metrics()

        # Generate summary report
        self._generate_validation_report()

        return self.validation_results

    def _validate_file_structure(self):
        """Ensure all required files exist for each year"""
        logger.info("Validating file structure...")

        required_tables = [
            "students",
            "teachers",
            "guardians",
            "classes",
            "enrollments",
            "assignments",
            "grades",
            "attendance",
            "payments",
            "school_calendar",
        ]

        missing_files = []
        for year in self.years:
            year_data = self.yearly_data[year]
            for table in required_tables:
                if table not in year_data:
                    missing_files.append(f"{year}: {table}.csv")

        if missing_files:
            self._add_failure("File Structure", f"Missing files: {missing_files}")
        else:
            self._add_success(
                "File Structure",
                f"All required files present for {len(self.years)} years",
            )

    def _validate_referential_integrity(self):
        """Check foreign key relationships"""
        logger.info("Validating referential integrity...")

        integrity_issues = []

        for year in self.years:
            data = self.yearly_data[year]

            # Students -> Grade Levels
            if "students" in data and "grade_levels" in data:
                valid_grades = set(data["grade_levels"]["grade_level_id"])
                student_grades = set(data["students"]["grade_level_id"])
                invalid_grades = student_grades - valid_grades
                if invalid_grades:
                    integrity_issues.append(
                        f"{year}: Invalid grade_level_ids in students: {invalid_grades}"
                    )

            # Enrollments -> Students and Classes
            if "enrollments" in data and "students" in data and "classes" in data:
                valid_students = set(data["students"]["student_id"])
                valid_classes = set(data["classes"]["class_id"])

                enrollment_students = set(data["enrollments"]["student_id"])
                enrollment_classes = set(data["enrollments"]["class_id"])

                invalid_students = enrollment_students - valid_students
                invalid_classes = enrollment_classes - valid_classes

                if invalid_students:
                    integrity_issues.append(
                        f"{year}: Invalid student_ids in enrollments: {len(invalid_students)} records"
                    )
                if invalid_classes:
                    integrity_issues.append(
                        f"{year}: Invalid class_ids in enrollments: {len(invalid_classes)} records"
                    )

            # Grades -> Students and Assignments
            if "grades" in data and "students" in data and "assignments" in data:
                valid_students = set(data["students"]["student_id"])
                valid_assignments = set(data["assignments"]["assignment_id"])

                grade_students = set(data["grades"]["student_id"])
                grade_assignments = set(data["grades"]["assignment_id"])

                invalid_students = grade_students - valid_students
                invalid_assignments = grade_assignments - valid_assignments

                if invalid_students:
                    integrity_issues.append(
                        f"{year}: Invalid student_ids in grades: {len(invalid_students)} records"
                    )
                if invalid_assignments:
                    integrity_issues.append(
                        f"{year}: Invalid assignment_ids in grades: {len(invalid_assignments)} records"
                    )

        if integrity_issues:
            self._add_failure(
                "Referential Integrity", f"{len(integrity_issues)} issues found"
            )
            for issue in integrity_issues[:5]:  # Show first 5
                logger.warning(f"  {issue}")
        else:
            self._add_success(
                "Referential Integrity", "All foreign key relationships valid"
            )

    def _validate_data_types(self):
        """Validate data types and ranges"""
        logger.info("Validating data types and ranges...")

        type_issues = []

        for year in self.years:
            data = self.yearly_data[year]

            # Check grade scores (0-100 range)
            if "grades" in data:
                grades_df = data["grades"]
                if "score" in grades_df.columns:
                    invalid_scores = grades_df[
                        (grades_df["score"] < 0) | (grades_df["score"] > 100)
                    ]
                    if len(invalid_scores) > 0:
                        type_issues.append(
                            f"{year}: {len(invalid_scores)} invalid grade scores (outside 0-100)"
                        )

            # Check attendance status values
            if "attendance" in data:
                attendance_df = data["attendance"]
                if "status" in attendance_df.columns:
                    valid_statuses = {
                        "Present",
                        "Absent",
                        "Tardy",
                        "Excused",
                        "Dismissed",
                    }
                    invalid_statuses = set(attendance_df["status"]) - valid_statuses
                    if invalid_statuses:
                        type_issues.append(
                            f"{year}: Invalid attendance statuses: {invalid_statuses}"
                        )

            # Check payment amounts (positive)
            if "payments" in data:
                payments_df = data["payments"]
                if "amount_paid" in payments_df.columns:
                    negative_payments = payments_df[payments_df["amount_paid"] <= 0]
                    if len(negative_payments) > 0:
                        type_issues.append(
                            f"{year}: {len(negative_payments)} non-positive payment amounts"
                        )

        if type_issues:
            self._add_failure("Data Types", f"{len(type_issues)} data type issues")
            for issue in type_issues[:3]:
                logger.warning(f"  {issue}")
        else:
            self._add_success("Data Types", "All data types and ranges valid")

    def _validate_enrollment_progression(self):
        """Validate student enrollment numbers follow expected patterns"""
        logger.info("Validating enrollment progression...")

        enrollment_stats = {}
        for year in self.years:
            if "students" in self.yearly_data[year]:
                enrollment_stats[year] = len(self.yearly_data[year]["students"])

        # Check for reasonable growth/decline patterns
        issues = []
        for i in range(1, len(self.years)):
            prev_year = self.years[i - 1]
            curr_year = self.years[i]

            prev_enrollment = enrollment_stats.get(prev_year, 0)
            curr_enrollment = enrollment_stats.get(curr_year, 0)

            if prev_enrollment > 0:
                change_pct = (curr_enrollment - prev_enrollment) / prev_enrollment
                if abs(change_pct) > 0.20:  # More than 20% change
                    issues.append(
                        f"{prev_year}->{curr_year}: {change_pct:.1%} enrollment change"
                    )

        self.validation_results["statistics"]["enrollment_by_year"] = enrollment_stats

        if issues:
            self._add_warning(
                "Enrollment Progression", f"Large enrollment changes: {issues}"
            )
        else:
            self._add_success(
                "Enrollment Progression",
                f"Enrollment progression realistic: {min(enrollment_stats.values())}-{max(enrollment_stats.values())} students",
            )

    def _validate_attendance_policies(self):
        """Validate 5% absence and 3% tardy rates"""
        logger.info("Validating attendance policies...")

        attendance_stats = {}

        for year in self.years:
            if "attendance" in self.yearly_data[year]:
                attendance_df = self.yearly_data[year]["attendance"]

                total_records = len(attendance_df)
                if total_records > 0:
                    absent_records = len(
                        attendance_df[
                            attendance_df["status"].isin(["Absent", "Excused"])
                        ]
                    )
                    tardy_records = len(
                        attendance_df[attendance_df["status"] == "Tardy"]
                    )

                    absent_rate = absent_records / total_records
                    tardy_rate = tardy_records / total_records

                    attendance_stats[year] = {
                        "absent_rate": absent_rate,
                        "tardy_rate": tardy_rate,
                        "total_records": total_records,
                    }

        # Check if rates are within expected ranges (5% ± 2% for absences, 3% ± 2% for tardies)
        policy_violations = []
        for year, stats in attendance_stats.items():
            if not (0.03 <= stats["absent_rate"] <= 0.07):
                policy_violations.append(
                    f"{year}: Absence rate {stats['absent_rate']:.1%} (expected ~5%)"
                )
            if not (0.01 <= stats["tardy_rate"] <= 0.05):
                policy_violations.append(
                    f"{year}: Tardy rate {stats['tardy_rate']:.1%} (expected ~3%)"
                )

        self.validation_results["statistics"]["attendance_rates"] = attendance_stats

        if policy_violations:
            self._add_warning(
                "Attendance Policies",
                f"Policy deviations: {len(policy_violations)} years",
            )
        else:
            self._add_success(
                "Attendance Policies",
                "Attendance rates comply with 5% absence, 3% tardy policy",
            )

    def _validate_grade_distributions(self):
        """Validate grade distributions follow 70-100 range with 85-90 median"""
        logger.info("Validating grade distributions...")

        grade_stats = {}

        for year in self.years:
            if "grades" in self.yearly_data[year]:
                grades_df = self.yearly_data[year]["grades"]

                if "score" in grades_df.columns and len(grades_df) > 0:
                    scores = grades_df["score"].dropna()

                    grade_stats[year] = {
                        "mean": scores.mean(),
                        "median": scores.median(),
                        "min": scores.min(),
                        "max": scores.max(),
                        "below_70_pct": len(scores[scores < 70]) / len(scores),
                        "perfect_pct": len(scores[scores >= 95]) / len(scores),
                        "total_grades": len(scores),
                    }

        # Validate against expected distributions
        distribution_issues = []
        for year, stats in grade_stats.items():
            # Check median in 85-90 range
            if not (82 <= stats["median"] <= 92):
                distribution_issues.append(
                    f"{year}: Median {stats['median']:.1f} outside 85-90 range"
                )

            # Check perfect grades ~3%
            if not (0.01 <= stats["perfect_pct"] <= 0.06):
                distribution_issues.append(
                    f"{year}: Perfect grades {stats['perfect_pct']:.1%} (expected ~3%)"
                )

            # Check failing grades 3-5%
            if stats["below_70_pct"] > 0.08:
                distribution_issues.append(
                    f"{year}: Below-70 grades {stats['below_70_pct']:.1%} (expected 3-5%)"
                )

        self.validation_results["statistics"]["grade_distributions"] = grade_stats

        if distribution_issues:
            self._add_warning(
                "Grade Distributions",
                f"Distribution issues: {len(distribution_issues)} years",
            )
        else:
            self._add_success(
                "Grade Distributions", "Grade distributions follow expected patterns"
            )

    def _validate_teacher_assignments(self):
        """Validate teacher-to-student ratios and assignments"""
        logger.info("Validating teacher assignments...")

        teacher_stats = {}

        for year in self.years:
            data = self.yearly_data[year]

            if "teachers" in data and "students" in data:
                num_teachers = len(data["teachers"])
                num_students = len(data["students"])

                student_teacher_ratio = (
                    num_students / num_teachers if num_teachers > 0 else 0
                )

                teacher_stats[year] = {
                    "teachers": num_teachers,
                    "students": num_students,
                    "ratio": student_teacher_ratio,
                }

        # Check for reasonable student-teacher ratios (8-12 students per teacher)
        ratio_issues = []
        for year, stats in teacher_stats.items():
            if not (6 <= stats["ratio"] <= 15):
                ratio_issues.append(
                    f"{year}: Ratio {stats['ratio']:.1f}:1 students per teacher"
                )

        self.validation_results["statistics"]["teacher_ratios"] = teacher_stats

        if ratio_issues:
            self._add_warning(
                "Teacher Assignments", f"Unusual ratios: {len(ratio_issues)} years"
            )
        else:
            self._add_success(
                "Teacher Assignments", "Student-teacher ratios within expected range"
            )

    def _validate_financial_data(self):
        """Validate payment patterns and amounts"""
        logger.info("Validating financial data...")

        financial_stats = {}

        for year in self.years:
            if "payments" in self.yearly_data[year]:
                payments_df = self.yearly_data[year]["payments"]

                if len(payments_df) > 0:
                    total_payments = payments_df["amount_paid"].sum()
                    avg_payment = payments_df["amount_paid"].mean()
                    num_payments = len(payments_df)

                    financial_stats[year] = {
                        "total_revenue": total_payments,
                        "avg_payment": avg_payment,
                        "num_payments": num_payments,
                    }

        self.validation_results["statistics"]["financial_summary"] = financial_stats
        self._add_success(
            "Financial Data", f"Payment data validated for {len(financial_stats)} years"
        )

    def _validate_student_progression(self):
        """Validate students progress through grades correctly"""
        logger.info("Validating student progression...")

        # Track students across years
        student_progressions = defaultdict(list)

        for year in self.years:
            if "students" in self.yearly_data[year]:
                students_df = self.yearly_data[year]["students"]
                for _, student in students_df.iterrows():
                    student_progressions[student["student_id"]].append(
                        {
                            "year": year,
                            "grade": student["grade_level_id"],
                            "name": f"{student['first_name']} {student['last_name']}",
                        }
                    )

        # Check for logical progressions
        progression_issues = []
        students_tracked = 0

        for student_id, progression in student_progressions.items():
            if len(progression) > 1:
                students_tracked += 1
                progression.sort(key=lambda x: x["year"])

                for i in range(1, len(progression)):
                    prev_grade = progression[i - 1]["grade"]
                    curr_grade = progression[i]["grade"]

                    # Students should advance one grade per year (or graduate)
                    if curr_grade != prev_grade + 1:
                        # Unless they graduated (grade 13 -> no longer present)
                        if not (prev_grade == 13):
                            progression_issues.append(
                                f"Student {student_id}: Grade {prev_grade} -> {curr_grade}"
                            )

        if progression_issues:
            self._add_warning(
                "Student Progression",
                f"{len(progression_issues)} irregular progressions out of {students_tracked} tracked",
            )
        else:
            self._add_success(
                "Student Progression",
                f"{students_tracked} students tracked with logical grade progression",
            )

    def _validate_teacher_continuity(self):
        """Validate teacher employment patterns"""
        logger.info("Validating teacher continuity...")

        # Track teachers across years
        teacher_continuity = defaultdict(list)

        for year in self.years:
            if "teachers" in self.yearly_data[year]:
                teachers_df = self.yearly_data[year]["teachers"]
                for _, teacher in teachers_df.iterrows():
                    teacher_continuity[teacher["teacher_id"]].append(
                        {
                            "year": year,
                            "name": f"{teacher['first_name']} {teacher['last_name']}",
                        }
                    )

        # Calculate retention statistics
        total_teacher_years = sum(len(years) for years in teacher_continuity.values())
        unique_teachers = len(teacher_continuity)
        avg_tenure = total_teacher_years / unique_teachers if unique_teachers > 0 else 0

        self.validation_results["statistics"]["teacher_continuity"] = {
            "unique_teachers": unique_teachers,
            "avg_tenure_years": avg_tenure,
            "total_teacher_years": total_teacher_years,
        }

        self._add_success(
            "Teacher Continuity",
            f"{unique_teachers} unique teachers, avg tenure {avg_tenure:.1f} years",
        )

    def _validate_curriculum_evolution(self):
        """Validate curriculum changes over time"""
        logger.info("Validating curriculum evolution...")

        # Track subjects by year
        subjects_by_year = {}

        for year in self.years:
            if "subjects" in self.yearly_data[year]:
                subjects_df = self.yearly_data[year]["subjects"]
                subjects_by_year[year] = set(subjects_df["name"].tolist())

        # Check for curriculum evolution
        curriculum_changes = []
        for i in range(1, len(self.years)):
            prev_year = self.years[i - 1]
            curr_year = self.years[i]

            if prev_year in subjects_by_year and curr_year in subjects_by_year:
                prev_subjects = subjects_by_year[prev_year]
                curr_subjects = subjects_by_year[curr_year]

                added = curr_subjects - prev_subjects
                removed = prev_subjects - curr_subjects

                if added or removed:
                    curriculum_changes.append(
                        {
                            "year": curr_year,
                            "added": list(added),
                            "removed": list(removed),
                        }
                    )

        self.validation_results["statistics"][
            "curriculum_evolution"
        ] = curriculum_changes

        if curriculum_changes:
            self._add_success(
                "Curriculum Evolution",
                f"{len(curriculum_changes)} curriculum updates over decade",
            )
        else:
            self._add_warning("Curriculum Evolution", "No curriculum changes detected")

    def _validate_demographic_distributions(self):
        """Validate demographic distributions"""
        logger.info("Validating demographic distributions...")

        demo_stats = {}

        for year in self.years:
            if "students" in self.yearly_data[year]:
                students_df = self.yearly_data[year]["students"]

                # Gender distribution
                gender_counts = students_df["gender"].value_counts()
                total_students = len(students_df)

                # Grade level distribution
                grade_counts = students_df["grade_level_id"].value_counts().sort_index()

                demo_stats[year] = {
                    "total_students": total_students,
                    "gender_distribution": gender_counts.to_dict(),
                    "grade_distribution": grade_counts.to_dict(),
                }

        self.validation_results["statistics"]["demographics"] = demo_stats
        self._add_success("Demographics", "Demographic distributions calculated")

    def _validate_academic_performance(self):
        """Validate academic performance metrics"""
        logger.info("Validating academic performance...")

        performance_stats = {}

        for year in self.years:
            if (
                "grades" in self.yearly_data[year]
                and "assignments" in self.yearly_data[year]
            ):
                grades_df = self.yearly_data[year]["grades"]
                assignments_df = self.yearly_data[year]["assignments"]

                # Calculate GPA equivalent
                if len(grades_df) > 0:
                    # Merge grades with assignments to get points_possible
                    merged = grades_df.merge(
                        assignments_df[["assignment_id", "points_possible"]],
                        on="assignment_id",
                        how="left",
                    )

                    # Calculate percentage scores (0-100 scale)
                merged["percentage"] = (
                    merged["score"] / merged["points_possible"]
                ) * 100

                performance_stats[year] = {
                    "avg_percentage": merged["percentage"].mean(),
                    "total_assignments": len(assignments_df),
                    "total_grades": len(grades_df),
                }

        self.validation_results["statistics"][
            "academic_performance"
        ] = performance_stats
        self._add_success("Academic Performance", "Performance metrics calculated")

    def _validate_operational_metrics(self):
        """Validate operational efficiency metrics"""
        logger.info("Validating operational metrics...")

        operational_stats = {}

        for year in self.years:
            data = self.yearly_data[year]

            metrics = {}

            # Classes per teacher
            if "classes" in data and "teachers" in data:
                num_classes = len(data["classes"])
                num_teachers = len(data["teachers"])
                metrics["classes_per_teacher"] = (
                    num_classes / num_teachers if num_teachers > 0 else 0
                )

            # Students per class
            if "enrollments" in data and "classes" in data:
                enrollments_per_class = data["enrollments"].groupby("class_id").size()
                metrics["avg_students_per_class"] = enrollments_per_class.mean()
                metrics["max_students_per_class"] = enrollments_per_class.max()

            # Assignments per class (should be ~70 per year)
            if "assignments" in data and "classes" in data:
                assignments_per_class = data["assignments"].groupby("class_id").size()
                metrics["avg_assignments_per_class"] = assignments_per_class.mean()

            operational_stats[year] = metrics

        self.validation_results["statistics"]["operational_metrics"] = operational_stats
        self._add_success(
            "Operational Metrics", "Operational efficiency metrics calculated"
        )

    def _add_success(self, category, message):
        """Add a successful validation"""
        self.validation_results["passed"].append(
            {"category": category, "message": message}
        )
        logger.info(f"✅ {category}: {message}")

    def _add_failure(self, category, message):
        """Add a failed validation"""
        self.validation_results["failed"].append(
            {"category": category, "message": message}
        )
        logger.error(f"❌ {category}: {message}")

    def _add_warning(self, category, message):
        """Add a warning"""
        self.validation_results["warnings"].append(
            {"category": category, "message": message}
        )
        logger.warning(f"⚠️  {category}: {message}")

    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 VALIDATION SUMMARY REPORT")
        logger.info("=" * 60)

        passed = len(self.validation_results["passed"])
        failed = len(self.validation_results["failed"])
        warnings = len(self.validation_results["warnings"])

        logger.info(f"✅ PASSED: {passed}")
        logger.info(f"❌ FAILED: {failed}")
        logger.info(f"⚠️  WARNINGS: {warnings}")

        if failed == 0:
            logger.info("\n🎉 DATA VALIDATION SUCCESSFUL!")
            logger.info("Your decade dataset meets all quality standards!")
        elif failed <= 2:
            logger.info("\n✅ DATA VALIDATION MOSTLY SUCCESSFUL")
            logger.info("Minor issues detected but data is usable")
        else:
            logger.info("\n⚠️  DATA VALIDATION ISSUES DETECTED")
            logger.info("Please review failed validations")

        # Key statistics summary
        stats = self.validation_results["statistics"]

        if "enrollment_by_year" in stats:
            enrollments = stats["enrollment_by_year"]
            logger.info(
                f"\n📈 ENROLLMENT RANGE: {min(enrollments.values())} - {max(enrollments.values())} students"
            )

        if "teacher_ratios" in stats:
            ratios = [s["ratio"] for s in stats["teacher_ratios"].values()]
            logger.info(
                f"👨‍🏫 STUDENT-TEACHER RATIO: {min(ratios):.1f} - {max(ratios):.1f}:1"
            )

        if "grade_distributions" in stats:
            medians = [s["median"] for s in stats["grade_distributions"].values()]
            logger.info(f"📊 GRADE MEDIANS: {min(medians):.1f} - {max(medians):.1f}")

        if "financial_summary" in stats:
            revenues = [s["total_revenue"] for s in stats["financial_summary"].values()]
            logger.info(
                f"💰 ANNUAL REVENUE RANGE: ${min(revenues):,.0f} - ${max(revenues):,.0f}"
            )

        logger.info("=" * 60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Validate Luminosity decade dataset")
    parser.add_argument(
        "--data-dir", default="../data/decade", help="Directory containing decade data"
    )
    parser.add_argument(
        "--save-report", default=None, help="Save detailed report to JSON file"
    )

    args = parser.parse_args()

    if not os.path.exists(args.data_dir):
        logger.error(f"Data directory not found: {args.data_dir}")
        return 1

    # Initialize validator
    validator = LuminosityDataValidator(args.data_dir)

    try:
        # Load and validate data
        validator.load_decade_data()
        results = validator.validate_all()

        # Save detailed report if requested
        if args.save_report:
            with open(args.save_report, "w") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Detailed report saved to {args.save_report}")

        # Return appropriate exit code
        if len(results["failed"]) == 0:
            return 0
        elif len(results["failed"]) <= 2:
            return 1
        else:
            return 2

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit(main())
