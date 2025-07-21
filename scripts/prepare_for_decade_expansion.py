#!/usr/bin/env python3
# flake8: noqa
"""
Luminosity Data Preparation & Validation Script

This script analyzes the current 2015-2016 data and prepares for decade expansion.
It validates data quality, identifies patterns, and creates baseline metrics.

Usage:
    python prepare_for_decade_expansion.py --data-dir ../data/clean_csv
"""

import argparse
import json
import logging
import os
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LuminosityDataAnalyzer:
    """Analyzes current Luminosity data and prepares for decade expansion"""

    def __init__(self, data_directory: str):
        self.data_dir = data_directory
        self.tables = {}
        self.analysis_results = {}
        self.validation_results = {}

    def load_all_data(self):
        """Load all CSV files into memory for analysis"""
        logger.info("Loading all data files...")

        csv_files = [f for f in os.listdir(self.data_dir) if f.endswith(".csv")]

        for csv_file in csv_files:
            table_name = csv_file.replace(".csv", "")
            file_path = os.path.join(self.data_dir, csv_file)

            try:
                df = pd.read_csv(file_path)
                self.tables[table_name] = df
                logger.info(
                    f"✅ Loaded {table_name}: {len(df)} rows, {len(df.columns)} columns"
                )
            except Exception as e:
                logger.error(f"❌ Failed to load {csv_file}: {str(e)}")

        logger.info(f"Successfully loaded {len(self.tables)} tables")
        return self.tables

    def analyze_baseline_data(self):
        """Comprehensive analysis of 2015-2016 baseline data"""
        logger.info("\n" + "=" * 50)
        logger.info("BASELINE DATA ANALYSIS (2015-2016)")
        logger.info("=" * 50)

        analysis = {
            "data_overview": self._analyze_data_overview(),
            "student_demographics": self._analyze_student_demographics(),
            "academic_structure": self._analyze_academic_structure(),
            "performance_patterns": self._analyze_performance_patterns(),
            "teacher_distribution": self._analyze_teacher_distribution(),
            "financial_patterns": self._analyze_financial_patterns(),
            "data_quality": self._validate_data_quality(),
        }

        self.analysis_results = analysis
        return analysis

    def _analyze_data_overview(self):
        """Basic overview of all tables and record counts"""
        overview = {}

        for table_name, df in self.tables.items():
            overview[table_name] = {
                "record_count": len(df),
                "column_count": len(df.columns),
                "columns": list(df.columns),
                "memory_usage_mb": round(
                    df.memory_usage(deep=True).sum() / 1024 / 1024, 2
                ),
            }

        # Calculate total records and relationships
        total_records = sum(info["record_count"] for info in overview.values())
        overview["summary"] = {
            "total_tables": len(overview),
            "total_records": total_records,
            "total_memory_mb": sum(
                info["memory_usage_mb"] for info in overview.values()
            ),
        }

        logger.info(
            f"Data Overview: {len(overview)} tables, {total_records:,} total records"
        )
        return overview

    def _analyze_student_demographics(self):
        """Analyze student population demographics"""
        if "students" not in self.tables:
            return {"error": "Students table not found"}

        students_df = self.tables["students"]

        demographics = {
            "total_students": len(students_df),
            "gender_distribution": students_df["gender"].value_counts().to_dict(),
            "grade_distribution": {},
            "age_analysis": {},
            "name_patterns": {},
        }

        # Grade level analysis
        if "grade_levels" in self.tables:
            grade_levels_df = self.tables["grade_levels"]
            grade_distribution = (
                students_df["grade_level_id"].value_counts().sort_index()
            )

            for grade_id, count in grade_distribution.items():
                grade_label = grade_levels_df[
                    grade_levels_df["grade_level_id"] == grade_id
                ]["label"].iloc[0]
                demographics["grade_distribution"][grade_label] = count

        # Age analysis (calculate from birth dates)
        try:
            students_df["date_of_birth"] = pd.to_datetime(students_df["date_of_birth"])
            today = pd.Timestamp.now()
            students_df["age"] = (today - students_df["date_of_birth"]).dt.days / 365.25

            demographics["age_analysis"] = {
                "mean_age": round(students_df["age"].mean(), 1),
                "min_age": round(students_df["age"].min(), 1),
                "max_age": round(students_df["age"].max(), 1),
                "age_by_grade": students_df.groupby("grade_level_id")["age"]
                .mean()
                .round(1)
                .to_dict(),
            }
        except Exception as e:
            demographics["age_analysis"] = {
                "error": f"Could not calculate ages: {str(e)}"
            }

        # Name pattern analysis
        demographics["name_patterns"] = {
            "unique_first_names": students_df["first_name"].nunique(),
            "unique_last_names": students_df["last_name"].nunique(),
            "most_common_first_names": students_df["first_name"]
            .value_counts()
            .head(5)
            .to_dict(),
            "most_common_last_names": students_df["last_name"]
            .value_counts()
            .head(5)
            .to_dict(),
        }

        logger.info(
            f"Student Demographics: {demographics['total_students']} students across {len(demographics['grade_distribution'])} grades"
        )
        return demographics

    def _analyze_academic_structure(self):
        """Analyze classes, enrollments, and academic organization"""
        academic = {
            "classes_overview": {},
            "enrollment_patterns": {},
            "subject_distribution": {},
            "teacher_assignments": {},
        }

        # Classes analysis
        if "classes" in self.tables:
            classes_df = self.tables["classes"]
            academic["classes_overview"] = {
                "total_classes": len(classes_df),
                "classes_by_grade": classes_df["grade_level_id"]
                .value_counts()
                .sort_index()
                .to_dict(),
                "classes_by_period": classes_df["period_id"]
                .value_counts()
                .sort_index()
                .to_dict(),
                "classes_by_term": classes_df["term_id"]
                .value_counts()
                .sort_index()
                .to_dict(),
            }

        # Enrollment analysis
        if "enrollments" in self.tables:
            enrollments_df = self.tables["enrollments"]
            academic["enrollment_patterns"] = {
                "total_enrollments": len(enrollments_df),
                "unique_students_enrolled": enrollments_df["student_id"].nunique(),
                "unique_classes_with_enrollment": enrollments_df["class_id"].nunique(),
                "avg_enrollments_per_student": round(
                    len(enrollments_df) / enrollments_df["student_id"].nunique(), 1
                ),
            }

        # Subject analysis
        if "subjects" in self.tables:
            subjects_df = self.tables["subjects"]
            academic["subject_distribution"] = {
                "total_subjects": len(subjects_df),
                "subjects_by_department": (
                    subjects_df[" department_id"].value_counts().to_dict()
                    if " department_id" in subjects_df.columns
                    else {}
                ),
            }

        # Teacher assignment analysis
        if "teachers" in self.tables and "classes" in self.tables:
            teachers_df = self.tables["teachers"]
            classes_df = self.tables["classes"]

            teacher_loads = classes_df["teacher_id"].value_counts()
            academic["teacher_assignments"] = {
                "total_teachers": len(teachers_df),
                "teachers_with_classes": teacher_loads.count(),
                "avg_classes_per_teacher": round(teacher_loads.mean(), 1),
                "max_classes_per_teacher": teacher_loads.max(),
                "min_classes_per_teacher": teacher_loads.min(),
            }

        logger.info(
            f"Academic Structure: {academic['classes_overview'].get('total_classes', 0)} classes, {academic['enrollment_patterns'].get('total_enrollments', 0)} enrollments"
        )
        return academic

    def _analyze_performance_patterns(self):
        """Analyze grades, attendance, and academic performance"""
        performance = {
            "grades_analysis": {},
            "attendance_patterns": {},
            "assignment_distribution": {},
        }

        # Grades analysis
        if "grades" in self.tables:
            grades_df = self.tables["grades"]

            performance["grades_analysis"] = {
                "total_grades": len(grades_df),
                "unique_students_with_grades": grades_df["student_id"].nunique(),
                "unique_assignments": grades_df["assignment_id"].nunique(),
                "score_statistics": {
                    "mean_score": round(grades_df["score"].mean(), 1),
                    "median_score": round(grades_df["score"].median(), 1),
                    "min_score": grades_df["score"].min(),
                    "max_score": grades_df["score"].max(),
                    "std_score": round(grades_df["score"].std(), 1),
                },
            }

            # Score distribution analysis
            if "assignments" in self.tables:
                assignments_df = self.tables["assignments"]
                grades_with_points = grades_df.merge(
                    assignments_df[["assignment_id", "points_possible"]],
                    on="assignment_id",
                    how="left",
                )
                grades_with_points["percentage"] = (
                    grades_with_points["score"] / grades_with_points["points_possible"]
                ) * 100

                performance["grades_analysis"]["percentage_statistics"] = {
                    "mean_percentage": round(
                        grades_with_points["percentage"].mean(), 1
                    ),
                    "median_percentage": round(
                        grades_with_points["percentage"].median(), 1
                    ),
                    "grades_90_plus": len(
                        grades_with_points[grades_with_points["percentage"] >= 90]
                    ),
                    "grades_below_70": len(
                        grades_with_points[grades_with_points["percentage"] < 70]
                    ),
                }

        # Attendance analysis
        if "attendance" in self.tables:
            attendance_df = self.tables["attendance"]

            attendance_counts = attendance_df["status"].value_counts()
            total_attendance = len(attendance_df)

            performance["attendance_patterns"] = {
                "total_attendance_records": total_attendance,
                "unique_students_tracked": attendance_df["student_id"].nunique(),
                "status_distribution": attendance_counts.to_dict(),
                "attendance_rates": {
                    "present_rate": round(
                        (attendance_counts.get("Present", 0) / total_attendance) * 100,
                        1,
                    ),
                    "absent_rate": round(
                        (attendance_counts.get("Absent", 0) / total_attendance) * 100, 1
                    ),
                    "tardy_rate": round(
                        (attendance_counts.get("Tardy", 0) / total_attendance) * 100, 1
                    ),
                },
            }

        # Assignment distribution
        if "assignments" in self.tables:
            assignments_df = self.tables["assignments"]

            performance["assignment_distribution"] = {
                "total_assignments": len(assignments_df),
                "assignments_by_category": (
                    assignments_df["category"].value_counts().to_dict()
                    if "category" in assignments_df.columns
                    else {}
                ),
                "points_distribution": {
                    "mean_points": round(assignments_df["points_possible"].mean(), 1),
                    "median_points": round(
                        assignments_df["points_possible"].median(), 1
                    ),
                    "min_points": assignments_df["points_possible"].min(),
                    "max_points": assignments_df["points_possible"].max(),
                },
            }

        logger.info(
            f"Performance Analysis: {performance['grades_analysis'].get('total_grades', 0)} grades, {performance['attendance_patterns'].get('total_attendance_records', 0)} attendance records"
        )
        return performance

    def _analyze_teacher_distribution(self):
        """Analyze teacher demographics and assignments"""
        teacher_analysis = {}

        if "teachers" in self.tables:
            teachers_df = self.tables["teachers"]

            teacher_analysis = {
                "total_teachers": len(teachers_df),
                "department_distribution": teachers_df["department_id"]
                .value_counts()
                .to_dict(),
                "name_patterns": {
                    "unique_first_names": teachers_df["first_name"].nunique(),
                    "unique_last_names": teachers_df["last_name"].nunique(),
                },
            }

            # Add department names if available
            if "departments" in self.tables:
                departments_df = self.tables["departments"]
                dept_names = {}
                for dept_id, count in teacher_analysis[
                    "department_distribution"
                ].items():
                    dept_name = departments_df[
                        departments_df["department_id"] == dept_id
                    ]["name"].iloc[0]
                    dept_names[dept_name] = count
                teacher_analysis["department_distribution_named"] = dept_names

        logger.info(
            f"Teacher Analysis: {teacher_analysis.get('total_teachers', 0)} teachers across {len(teacher_analysis.get('department_distribution', {}))} departments"
        )
        return teacher_analysis

    def _analyze_financial_patterns(self):
        """Analyze payments and fee structures"""
        financial = {}

        if "payments" in self.tables:
            payments_df = self.tables["payments"]

            financial["payments_analysis"] = {
                "total_payments": len(payments_df),
                "total_amount_paid": payments_df["amount_paid"].sum(),
                "unique_guardians_paying": payments_df["guardian_id"].nunique(),
                "payment_statistics": {
                    "mean_payment": round(payments_df["amount_paid"].mean(), 2),
                    "median_payment": round(payments_df["amount_paid"].median(), 2),
                    "min_payment": payments_df["amount_paid"].min(),
                    "max_payment": payments_df["amount_paid"].max(),
                },
            }

        if "fee_types" in self.tables:
            fee_types_df = self.tables["fee_types"]

            financial["fee_structure"] = {
                "total_fee_types": len(fee_types_df),
                "fee_types_breakdown": fee_types_df[
                    ["name", "amount", "frequency"]
                ].to_dict("records"),
            }

        logger.info(
            f"Financial Analysis: {financial.get('payments_analysis', {}).get('total_payments', 0)} payments totaling ${financial.get('payments_analysis', {}).get('total_amount_paid', 0):,.2f}"
        )
        return financial

    def _validate_data_quality(self):
        """Comprehensive data quality validation"""
        validation = {
            "referential_integrity": {},
            "data_completeness": {},
            "data_consistency": {},
            "business_rule_compliance": {},
        }

        # Referential integrity checks
        validation["referential_integrity"] = self._check_referential_integrity()

        # Data completeness checks
        validation["data_completeness"] = self._check_data_completeness()

        # Data consistency checks
        validation["data_consistency"] = self._check_data_consistency()

        # Business rule compliance
        validation["business_rule_compliance"] = self._check_business_rules()

        # Overall quality score
        validation["quality_score"] = self._calculate_quality_score(validation)

        logger.info(f"Data Quality Score: {validation['quality_score']:.1f}/100")
        return validation

    def _check_referential_integrity(self):
        """Check foreign key relationships"""
        integrity_issues = []

        # Student -> Grade Level relationship
        if "students" in self.tables and "grade_levels" in self.tables:
            students_df = self.tables["students"]
            grade_levels_df = self.tables["grade_levels"]

            invalid_grades = students_df[
                ~students_df["grade_level_id"].isin(grade_levels_df["grade_level_id"])
            ]
            if not invalid_grades.empty:
                integrity_issues.append(
                    f"Students with invalid grade_level_id: {len(invalid_grades)}"
                )

        # Enrollments -> Students relationship
        if "enrollments" in self.tables and "students" in self.tables:
            enrollments_df = self.tables["enrollments"]
            students_df = self.tables["students"]

            invalid_student_enrollments = enrollments_df[
                ~enrollments_df["student_id"].isin(students_df["student_id"])
            ]
            if not invalid_student_enrollments.empty:
                integrity_issues.append(
                    f"Enrollments with invalid student_id: {len(invalid_student_enrollments)}"
                )

        # Grades -> Students relationship
        if "grades" in self.tables and "students" in self.tables:
            grades_df = self.tables["grades"]
            students_df = self.tables["students"]

            invalid_grade_students = grades_df[
                ~grades_df["student_id"].isin(students_df["student_id"])
            ]
            if not invalid_grade_students.empty:
                integrity_issues.append(
                    f"Grades with invalid student_id: {len(invalid_grade_students)}"
                )

        return {
            "issues_found": len(integrity_issues),
            "issues": integrity_issues,
            "status": "PASS" if len(integrity_issues) == 0 else "FAIL",
        }

    def _check_data_completeness(self):
        """Check for missing required data"""
        completeness_issues = []

        for table_name, df in self.tables.items():
            # Check for completely empty tables
            if len(df) == 0:
                completeness_issues.append(f"Table {table_name} is empty")
                continue

            # Check for null values in key columns
            null_counts = df.isnull().sum()
            for column, null_count in null_counts.items():
                if null_count > 0:
                    percentage = (null_count / len(df)) * 100
                    if percentage > 10:  # More than 10% null values
                        completeness_issues.append(
                            f"{table_name}.{column}: {percentage:.1f}% null values"
                        )

        return {
            "issues_found": len(completeness_issues),
            "issues": completeness_issues,
            "status": "PASS" if len(completeness_issues) == 0 else "WARN",
        }

    def _check_data_consistency(self):
        """Check for data consistency issues"""
        consistency_issues = []

        # Check age-grade alignment
        if "students" in self.tables:
            students_df = self.tables["students"]

            try:
                students_df["date_of_birth"] = pd.to_datetime(
                    students_df["date_of_birth"]
                )
                today = pd.Timestamp.now()
                students_df["age"] = (
                    today - students_df["date_of_birth"]
                ).dt.days / 365.25

                # Check for age-grade mismatches
                grade_age_map = {
                    1: (5, 6),
                    2: (6, 7),
                    3: (7, 8),
                    4: (8, 9),
                    5: (9, 10),
                    6: (10, 11),
                    7: (11, 12),
                    8: (12, 13),
                    9: (13, 14),
                    10: (14, 15),
                    11: (15, 16),
                    12: (16, 17),
                    13: (17, 18),
                }

                mismatches = 0
                for _, student in students_df.iterrows():
                    grade = student["grade_level_id"]
                    age = student["age"]
                    if grade in grade_age_map:
                        min_age, max_age = grade_age_map[grade]
                        if not (min_age <= age <= max_age + 2):  # Allow 2-year buffer
                            mismatches += 1

                if mismatches > 0:
                    consistency_issues.append(
                        f"Age-grade mismatches: {mismatches} students"
                    )

            except Exception as e:
                consistency_issues.append(
                    f"Could not validate age-grade consistency: {str(e)}"
                )

        # Check gender-name alignment (basic check)
        if "students" in self.tables:
            students_df = self.tables["students"]

            # Very basic check for obvious mismatches (this is not foolproof)
            male_names_with_female_gender = students_df[
                (students_df["first_name"].str.endswith(("a", "ia", "lyn")))
                & (students_df["gender"] == "M")
            ]
            if len(male_names_with_female_gender) > 5:  # Allow some exceptions
                consistency_issues.append(
                    f"Potential gender-name mismatches: {len(male_names_with_female_gender)} cases"
                )

        return {
            "issues_found": len(consistency_issues),
            "issues": consistency_issues,
            "status": "PASS" if len(consistency_issues) == 0 else "WARN",
        }

    def _check_business_rules(self):
        """Check compliance with documented business rules"""
        business_rule_issues = []

        # Check attendance rate compliance (should be ~5% absence)
        if "attendance" in self.tables:
            attendance_df = self.tables["attendance"]
            total_records = len(attendance_df)
            absent_records = len(attendance_df[attendance_df["status"] == "Absent"])
            absence_rate = (absent_records / total_records) * 100

            if not (3 <= absence_rate <= 7):  # Allow 3-7% range
                business_rule_issues.append(
                    f"Absence rate {absence_rate:.1f}% outside expected 5% range"
                )

        # Check grade distribution (should follow 70-100 range with ~87% median)
        if "grades" in self.tables and "assignments" in self.tables:
            grades_df = self.tables["grades"]
            assignments_df = self.tables["assignments"]

            grades_with_points = grades_df.merge(
                assignments_df[["assignment_id", "points_possible"]],
                on="assignment_id",
                how="left",
            )
            grades_with_points["percentage"] = (
                grades_with_points["score"] / grades_with_points["points_possible"]
            ) * 100

            median_percentage = grades_with_points["percentage"].median()
            if not (80 <= median_percentage <= 95):
                business_rule_issues.append(
                    f"Grade median {median_percentage:.1f}% outside expected 85-90% range"
                )

            low_grades = len(grades_with_points[grades_with_points["percentage"] < 70])
            low_grade_rate = (low_grades / len(grades_with_points)) * 100
            if low_grade_rate > 10:  # More than 10% failing
                business_rule_issues.append(
                    f"Failing grade rate {low_grade_rate:.1f}% higher than expected 3-5%"
                )

        return {
            "issues_found": len(business_rule_issues),
            "issues": business_rule_issues,
            "status": "PASS" if len(business_rule_issues) == 0 else "WARN",
        }

    def _calculate_quality_score(self, validation_results):
        """Calculate overall data quality score (0-100)"""
        scores = []

        # Referential integrity (critical - 40% weight)
        integrity_score = (
            100
            if validation_results["referential_integrity"]["status"] == "PASS"
            else 0
        )
        scores.append(integrity_score * 0.4)

        # Data completeness (important - 30% weight)
        completeness_score = (
            100 if validation_results["data_completeness"]["status"] == "PASS" else 70
        )
        scores.append(completeness_score * 0.3)

        # Data consistency (important - 20% weight)
        consistency_score = (
            100 if validation_results["data_consistency"]["status"] == "PASS" else 80
        )
        scores.append(consistency_score * 0.2)

        # Business rule compliance (nice to have - 10% weight)
        business_score = (
            100
            if validation_results["business_rule_compliance"]["status"] == "PASS"
            else 90
        )
        scores.append(business_score * 0.1)

        return sum(scores)

    def create_decade_expansion_plan(self):
        """Create specific plan for decade expansion based on current data"""
        plan = {
            "baseline_summary": self._create_baseline_summary(),
            "expansion_strategy": self._create_expansion_strategy(),
            "data_migration_plan": self._create_migration_plan(),
            "quality_assurance_plan": self._create_qa_plan(),
            "timeline": self._create_timeline(),
        }

        return plan

    def _create_baseline_summary(self):
        """Summary of current data to inform expansion"""
        summary = {
            "data_ready_for_expansion": True,
            "baseline_year": "2015-2016",
            "total_students": len(self.tables.get("students", [])),
            "total_teachers": len(self.tables.get("teachers", [])),
            "total_classes": len(self.tables.get("classes", [])),
            "data_quality_score": self.validation_results.get("quality_score", 0),
            "critical_issues": [],
        }

        # Check if data is ready for expansion
        if (
            self.validation_results.get("referential_integrity", {}).get("status")
            != "PASS"
        ):
            summary["data_ready_for_expansion"] = False
            summary["critical_issues"].append(
                "Referential integrity failures must be fixed"
            )

        if summary["total_students"] < 100:
            summary["data_ready_for_expansion"] = False
            summary["critical_issues"].append(
                "Insufficient student population for realistic expansion"
            )

        return summary

    def _create_expansion_strategy(self):
        """Strategy for expanding to 10 years"""
        current_students = len(self.tables.get("students", []))

        strategy = {
            "approach": "gradual_growth",
            "target_enrollment_by_year": {},
            "teacher_scaling_plan": {},
            "curriculum_evolution": {},
            "infrastructure_needs": {},
        }

        # Calculate enrollment targets (realistic growth)
        base_enrollment = current_students
        for year in range(2016, 2026):
            if year <= 2019:
                growth_rate = 1.02  # 2% annual growth
            elif year == 2020:
                growth_rate = 0.95  # COVID impact
            elif year <= 2022:
                growth_rate = 1.08  # Recovery bounce
            else:
                growth_rate = 1.01  # Stable growth

            base_enrollment = int(base_enrollment * growth_rate)
            strategy["target_enrollment_by_year"][year] = base_enrollment

        # Teacher scaling (maintain 8:1 student-teacher ratio)
        for year, enrollment in strategy["target_enrollment_by_year"].items():
            target_teachers = max(60, int(enrollment / 8))
            strategy["teacher_scaling_plan"][year] = target_teachers

        return strategy

    def _create_migration_plan(self):
        """Plan for migrating data to decade-ready structure"""
        return {
            "phase_1": "Backup current data and create decade schema",
            "phase_2": "Generate years 2016-2020 (including COVID impact)",
            "phase_3": "Generate years 2021-2025 (recovery and growth)",
            "phase_4": "Validate complete decade and optimize performance",
            "estimated_timeline": "2-3 weeks",
            "resource_requirements": {
                "storage": "3-5 GB additional space",
                "processing_time": "4-6 hours for complete generation",
                "validation_time": "1-2 hours per year",
            },
        }

    def _create_qa_plan(self):
        """Quality assurance plan for decade data"""
        return {
            "validation_checkpoints": [
                "After each year generation",
                "After 5-year milestone",
                "Final comprehensive validation",
            ],
            "key_metrics_to_track": [
                "Student progression accuracy",
                "Teacher retention realism",
                "Grade distribution consistency",
                "Attendance pattern compliance",
                "Financial data accuracy",
            ],
            "automated_tests": [
                "Referential integrity checks",
                "Business rule compliance",
                "Statistical distribution validation",
                "Longitudinal consistency checks",
            ],
        }

    def _create_timeline(self):
        """Detailed timeline for decade expansion"""
        return {
            "week_1": [
                "Complete current data analysis",
                "Set up decade generation environment",
                "Create backup of current data",
            ],
            "week_2": [
                "Generate and validate years 2016-2018",
                "Implement quality assurance framework",
                "Test single-year generation pipeline",
            ],
            "week_3": [
                "Generate years 2019-2022 (including COVID)",
                "Validate major transitions and events",
                "Optimize performance for large datasets",
            ],
            "week_4": [
                "Generate years 2023-2025",
                "Complete final validation",
                "Deploy enhanced dashboard and analytics",
            ],
        }

    def generate_report(self, output_file: str = None):
        """Generate comprehensive analysis report"""
        report = {
            "analysis_date": datetime.now().isoformat(),
            "baseline_data_analysis": self.analysis_results,
            "data_validation_results": self.validation_results,
            "decade_expansion_plan": self.create_decade_expansion_plan(),
            "recommendations": self._generate_recommendations(),
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Analysis report saved to: {output_file}")

        return report

    def _generate_recommendations(self):
        """Generate specific recommendations for improvement"""
        recommendations = []

        # Data quality recommendations
        if self.validation_results.get("quality_score", 0) < 90:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Data Quality",
                    "recommendation": "Address data quality issues before decade expansion",
                    "details": "Fix referential integrity and consistency issues identified in validation",
                }
            )

        # Performance recommendations
        total_records = sum(len(df) for df in self.tables.values())
        if total_records > 50000:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "Performance",
                    "recommendation": "Implement database indexing strategy",
                    "details": "Large dataset will benefit from proper indexing for decade queries",
                }
            )

        # Expansion readiness
        if len(self.tables.get("students", [])) > 400:
            recommendations.append(
                {
                    "priority": "LOW",
                    "category": "Expansion",
                    "recommendation": "Student population ready for realistic decade expansion",
                    "details": "Current population size supports believable 10-year growth patterns",
                }
            )

        return recommendations


def main():
    """Main function to run the data preparation analysis"""
    parser = argparse.ArgumentParser(
        description="Analyze Luminosity data and prepare for decade expansion"
    )
    parser.add_argument(
        "--data-dir", default="../data/clean_csv", help="Directory containing CSV files"
    )
    parser.add_argument(
        "--output-report",
        default="./analysis_report.json",
        help="Output file for analysis report",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize analyzer
    analyzer = LuminosityDataAnalyzer(args.data_dir)

    # Load and analyze data
    try:
        logger.info("Starting Luminosity data analysis...")

        # Load all data
        analyzer.load_all_data()

        # Perform comprehensive analysis
        analysis_results = analyzer.analyze_baseline_data()

        # Generate final report
        report = analyzer.generate_report(args.output_report)

        # Print summary
        print("\n" + "=" * 60)
        print("LUMINOSITY DATA ANALYSIS COMPLETE")
        print("=" * 60)

        # Key findings
        students = analysis_results["student_demographics"]["total_students"]
        teachers = analysis_results["teacher_distribution"]["total_teachers"]
        quality_score = analysis_results["data_quality"]["quality_score"]

        print(f"📊 Baseline Data (2015-2016):")
        print(f"   Students: {students:,}")
        print(f"   Teachers: {teachers:,}")
        print(f"   Data Quality Score: {quality_score:.1f}/100")

        # Expansion readiness
        expansion_plan = report["decade_expansion_plan"]
        ready_for_expansion = expansion_plan["baseline_summary"][
            "data_ready_for_expansion"
        ]

        print(f"\n🚀 Decade Expansion Readiness:")
        print(f"   Status: {'✅ READY' if ready_for_expansion else '❌ NOT READY'}")

        if not ready_for_expansion:
            print(f"   Critical Issues:")
            for issue in expansion_plan["baseline_summary"]["critical_issues"]:
                print(f"      - {issue}")
        else:
            print(
                f"   Target 2025 Enrollment: {expansion_plan['expansion_strategy']['target_enrollment_by_year'].get(2025, 'TBD'):,}"
            )
            print(
                f"   Estimated Timeline: {expansion_plan['data_migration_plan']['estimated_timeline']}"
            )

        # Next steps
        print(f"\n📋 Recommended Next Steps:")
        recommendations = report["recommendations"]
        for i, rec in enumerate(recommendations[:3], 1):  # Show top 3 recommendations
            print(f"   {i}. [{rec['priority']}] {rec['recommendation']}")

        print(f"\n📄 Full analysis report saved to: {args.output_report}")
        print(f"🎯 Ready to begin decade expansion planning!")

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
