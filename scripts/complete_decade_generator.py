#!/usr/bin/env python3
# flake8: noqa
"""
Luminosity School Management System - COMPLETE 10-Year Historical Data Generator

This script generates ALL tables for realistic historical data for 2016-2025, building upon
the existing 2015-2016 baseline data. It handles student progression, teacher career changes,
curriculum evolution, administrative records, financial data, and ALL missing components.

Usage:
    python complete_decade_generator.py --start-year 2016 --end-year 2025
"""

import argparse
import json
import logging
import os
import random
from dataclasses import dataclass
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


@dataclass
class SchoolYearConfig:
    """Configuration for a specific school year"""

    year: int
    enrollment_target: int
    graduation_count: int
    new_kindergarten_count: int
    teacher_turnover_rate: float
    curriculum_changes: List[str]
    major_events: List[str]
    technology_updates: List[str]
    fee_adjustments: Dict[str, float]


class StudentRegistry:
    """Manages student lifecycle across multiple years"""

    def __init__(self):
        self.active_students = {}
        self.graduated_students = {}
        self.transferred_students = {}
        self.student_id_counter = 1
        self.family_registry = {}  # Track sibling relationships

    def load_baseline_students(self, students_df):
        """Load 2015-2016 students as baseline"""
        for _, student in students_df.iterrows():
            self.active_students[student["student_id"]] = {
                "student_id": student["student_id"],
                "first_name": student["first_name"],
                "last_name": student["last_name"],
                "gender": student["gender"],
                "date_of_birth": student["date_of_birth"],
                "grade_level_id": student["grade_level_id"],
                "enrollment_year": 2015,
                "family_id": f"FAM{student['student_id']//3}",  # Approximate family grouping
            }
            self.student_id_counter = max(
                self.student_id_counter, student["student_id"] + 1
            )

    def advance_grade_levels(self, year):
        """Advance all continuing students to next grade"""
        graduated = []
        advanced = []

        for student_id, student in list(self.active_students.items()):
            current_grade = student["grade_level_id"]

            if current_grade >= 13:  # 12th grade graduates
                graduated.append(student)
                self.graduated_students[student_id] = {
                    **student,
                    "graduation_year": year,
                }
                del self.active_students[student_id]
            else:
                student["grade_level_id"] = current_grade + 1
                advanced.append(student)

        logger.info(
            f"Year {year}: {len(graduated)} graduated, {len(advanced)} advanced"
        )
        return graduated, advanced

    def enroll_new_kindergarteners(self, year, count):
        """Add new kindergarten students"""
        fake = Faker()
        new_students = []

        for _ in range(count):
            # Generate realistic birth date for kindergartener (5 years old)
            birth_year = year - 5
            start_date = datetime(birth_year - 1, 9, 1).date()
            end_date = datetime(birth_year, 8, 31).date()
            birth_date = fake.date_between(start_date=start_date, end_date=end_date)

            gender = random.choice(["M", "F"])
            first_name = (
                fake.first_name_male() if gender == "M" else fake.first_name_female()
            )

            # Check for sibling enrollment (20% chance of having sibling already enrolled)
            family_id = None
            if random.random() < 0.20:
                existing_families = [
                    s["family_id"] for s in self.active_students.values()
                ]
                if existing_families:
                    family_id = random.choice(existing_families)
                    # Use same last name as sibling
                    sibling = next(
                        s
                        for s in self.active_students.values()
                        if s["family_id"] == family_id
                    )
                    last_name = sibling["last_name"]
                else:
                    family_id = f"FAM{self.student_id_counter//3}"
                    last_name = fake.last_name()
            else:
                family_id = f"FAM{self.student_id_counter//3}"
                last_name = fake.last_name()

            student = {
                "student_id": self.student_id_counter,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "date_of_birth": birth_date.strftime("%Y-%m-%d"),
                "grade_level_id": 1,  # Kindergarten
                "enrollment_year": year,
                "family_id": family_id,
            }

            self.active_students[self.student_id_counter] = student
            new_students.append(student)
            self.student_id_counter += 1

        logger.info(f"Year {year}: Enrolled {len(new_students)} new kindergarteners")
        return new_students

    def process_transfers(
        self, year, transfer_in_count, transfer_out_count, guardian_registry
    ):
        """Handle mid-year transfers in and out"""
        transfers_in = []
        transfers_out = []

        # Transfer out (random selection of current students)
        if transfer_out_count > 0:
            transfer_candidates = list(self.active_students.keys())
            transfer_out_ids = random.sample(
                transfer_candidates, min(transfer_out_count, len(transfer_candidates))
            )

            for student_id in transfer_out_ids:
                student = self.active_students[student_id]
                transfers_out.append(student)
                self.transferred_students[student_id] = {
                    **student,
                    "transfer_year": year,
                }

                # Remove student's guardians when they transfer out
                guardian_registry.remove_student_guardians(student_id)

                del self.active_students[student_id]

        # Transfer in (new students at various grade levels)
        fake = Faker()
        for _ in range(transfer_in_count):
            grade_level = random.randint(1, 12)  # K-11 (no 12th grade transfers)
            student_age = 5 + grade_level - 1
            birth_year = year - student_age

            start_date = datetime(birth_year - 1, 9, 1).date()
            end_date = datetime(birth_year, 8, 31).date()
            birth_date = fake.date_between(start_date=start_date, end_date=end_date)

            gender = random.choice(["M", "F"])
            first_name = (
                fake.first_name_male() if gender == "M" else fake.first_name_female()
            )

            student = {
                "student_id": self.student_id_counter,
                "first_name": first_name,
                "last_name": fake.last_name(),
                "gender": gender,
                "date_of_birth": birth_date.strftime("%Y-%m-%d"),
                "grade_level_id": grade_level,
                "enrollment_year": year,
                "family_id": f"FAM{self.student_id_counter//3}",
                "is_transfer": True,
            }

            self.active_students[self.student_id_counter] = student
            transfers_in.append(student)

            # Generate guardians for transfer students immediately
            guardian_registry.generate_guardians_for_students([student])

            self.student_id_counter += 1

        logger.info(
            f"Year {year}: {len(transfers_in)} transferred in, {len(transfers_out)} transferred out"
        )
        return transfers_in, transfers_out


class TeacherRegistry:
    """Manages teacher hiring, retirement, and career progression"""

    def __init__(self):
        self.active_teachers = {}
        self.retired_teachers = {}
        self.former_teachers = {}
        self.teacher_id_counter = 1

    def load_baseline_teachers(self, teachers_df):
        """Load 2015-2016 teachers as baseline"""
        for _, teacher in teachers_df.iterrows():
            self.active_teachers[teacher["teacher_id"]] = {
                "teacher_id": teacher["teacher_id"],
                "first_name": teacher["first_name"],
                "last_name": teacher["last_name"],
                "department_id": teacher["department_id"],
                "hire_year": random.randint(
                    2005, 2015
                ),  # Assume hired within last 10 years
                "years_experience": random.randint(1, 20),
                "position_level": random.choice(
                    ["Teacher", "Senior Teacher", "Department Head"]
                ),
            }
            self.teacher_id_counter = max(
                self.teacher_id_counter, teacher["teacher_id"] + 1
            )

    def process_annual_changes(self, year, target_teacher_count, turnover_rate):
        """Handle teacher retirements, resignations, and new hires"""
        retirements = []
        resignations = []
        new_hires = []

        current_count = len(self.active_teachers)
        expected_departures = int(current_count * turnover_rate)

        # Determine who leaves (prioritize older/more experienced teachers for retirement)
        departure_candidates = list(self.active_teachers.values())
        departure_candidates.sort(key=lambda t: t["years_experience"], reverse=True)

        for i in range(min(expected_departures, len(departure_candidates))):
            teacher = departure_candidates[i]

            if teacher["years_experience"] >= 25 or random.random() < 0.3:
                # Retirement
                retirements.append(teacher)
                self.retired_teachers[teacher["teacher_id"]] = {
                    **teacher,
                    "retirement_year": year,
                }
            else:
                # Resignation/career change
                resignations.append(teacher)
                self.former_teachers[teacher["teacher_id"]] = {
                    **teacher,
                    "departure_year": year,
                }

            del self.active_teachers[teacher["teacher_id"]]

        # Hire new teachers to reach target count
        fake = Faker()
        new_hire_count = target_teacher_count - len(self.active_teachers)

        department_needs = self._assess_department_needs()

        for _ in range(max(0, new_hire_count)):
            department_id = random.choices(
                list(department_needs.keys()), weights=list(department_needs.values())
            )[0]

            gender = random.choice(["M", "F"])
            first_name = (
                fake.first_name_male() if gender == "M" else fake.first_name_female()
            )

            teacher = {
                "teacher_id": self.teacher_id_counter,
                "first_name": first_name,
                "last_name": fake.last_name(),
                "department_id": department_id,
                "hire_year": year,
                "years_experience": random.randint(
                    0, 5
                ),  # New hires typically have less experience
                "position_level": "Teacher",
            }

            self.active_teachers[self.teacher_id_counter] = teacher
            new_hires.append(teacher)
            self.teacher_id_counter += 1

        # Age existing teachers
        for teacher in self.active_teachers.values():
            teacher["years_experience"] += 1

        logger.info(
            f"Year {year}: {len(retirements)} retired, {len(resignations)} resigned, {len(new_hires)} hired"
        )
        return retirements, resignations, new_hires

    def _assess_department_needs(self):
        """Determine which departments need more teachers"""
        department_counts = {}
        for teacher in self.active_teachers.values():
            dept_id = teacher["department_id"]
            department_counts[dept_id] = department_counts.get(dept_id, 0) + 1

        # Weight departments by need (inverse of current count)
        total_teachers = sum(department_counts.values())
        department_weights = {}

        for dept_id in range(1, 10):  # Departments 1-9
            current_count = department_counts.get(dept_id, 0)
            ideal_count = total_teachers / 9  # Even distribution
            need_factor = max(1, ideal_count - current_count)
            department_weights[dept_id] = need_factor

        return department_weights


class GuardianRegistry:
    """Manages guardian relationships and family structures"""

    def __init__(self):
        self.guardians = {}
        self.student_guardians = {}
        self.guardian_id_counter = 1
        self.transferred_guardians = {}  # Track guardians who transferred out

    def remove_student_guardians(self, student_id):
        """Remove guardians when student transfers out"""
        # Find guardians for this student
        student_guardian_relationships = [
            sg
            for sg in self.student_guardians.values()
            if sg.get("student_id") == student_id
        ]

        for relationship in student_guardian_relationships:
            guardian_id = relationship["guardian_id"]

            # Check if this guardian has other students still enrolled
            other_students = [
                sg
                for sg in self.student_guardians.values()
                if sg.get("guardian_id") == guardian_id
                and sg.get("student_id") != student_id
            ]

            if not other_students:
                # No other students, remove guardian completely
                if guardian_id in self.guardians:
                    self.transferred_guardians[guardian_id] = self.guardians[
                        guardian_id
                    ]
                    del self.guardians[guardian_id]

            # Remove this specific student-guardian relationship
            if student_id in self.student_guardians:
                del self.student_guardians[student_id]

    def generate_guardians_for_students(self, students):
        """Generate guardians following the 65% shared name and family structure rules"""
        new_guardians = []
        new_student_guardians = []

        for student in students:
            student_id = student["student_id"]
            student_last_name = student["last_name"]
            family_id = student.get("family_id", f"FAM{student_id//3}")

            # Skip if this student already has guardians
            if student_id in self.student_guardians:
                continue

            # Check if family already has guardians (for siblings)
            existing_family_guardians = []
            for sg in self.student_guardians.values():
                if sg.get("family_id") == family_id:
                    existing_family_guardians.append(sg)

            if existing_family_guardians:
                # Use existing family guardians for siblings
                for existing_sg in existing_family_guardians:
                    new_relationship = {
                        "student_id": student_id,
                        "guardian_id": existing_sg["guardian_id"],
                        "guardian_type_id": existing_sg["guardian_type_id"],
                        "family_id": family_id,
                    }
                    new_student_guardians.append(new_relationship)
                    self.student_guardians[student_id] = new_relationship
                continue

            # Determine if this student shares last name with guardians (65% chance)
            shares_last_name = random.random() < 0.65

            if shares_last_name:
                # Determine family structure for parent families
                rand = random.random()
                if rand < 0.60:  # 60% two-parent families
                    # Two-parent family
                    family_last_name = student_last_name
                    fake = Faker()

                    # Mother
                    mother = {
                        "guardian_id": self.guardian_id_counter,
                        "first_name": fake.first_name_female(),
                        "last_name": family_last_name,
                        "email": fake.email(),
                        "phone": fake.phone_number(),
                    }
                    new_guardians.append(mother)
                    self.guardians[self.guardian_id_counter] = mother

                    mother_relationship = {
                        "student_id": student_id,
                        "guardian_id": self.guardian_id_counter,
                        "guardian_type_id": 1,  # Mother
                        "family_id": family_id,
                    }
                    new_student_guardians.append(mother_relationship)
                    self.student_guardians[f"{student_id}_1"] = mother_relationship
                    self.guardian_id_counter += 1

                    # Father
                    father = {
                        "guardian_id": self.guardian_id_counter,
                        "first_name": fake.first_name_male(),
                        "last_name": family_last_name,
                        "email": fake.email(),
                        "phone": fake.phone_number(),
                    }
                    new_guardians.append(father)
                    self.guardians[self.guardian_id_counter] = father

                    father_relationship = {
                        "student_id": student_id,
                        "guardian_id": self.guardian_id_counter,
                        "guardian_type_id": 2,  # Father
                        "family_id": family_id,
                    }
                    new_student_guardians.append(father_relationship)
                    self.student_guardians[f"{student_id}_2"] = father_relationship
                    self.guardian_id_counter += 1

                elif rand < 0.95:  # 35% single mother families
                    # Single mother
                    fake = Faker()
                    mother = {
                        "guardian_id": self.guardian_id_counter,
                        "first_name": fake.first_name_female(),
                        "last_name": student_last_name,
                        "email": fake.email(),
                        "phone": fake.phone_number(),
                    }
                    new_guardians.append(mother)
                    self.guardians[self.guardian_id_counter] = mother

                    mother_relationship = {
                        "student_id": student_id,
                        "guardian_id": self.guardian_id_counter,
                        "guardian_type_id": 1,  # Mother
                        "family_id": family_id,
                    }
                    new_student_guardians.append(mother_relationship)
                    self.student_guardians[student_id] = mother_relationship
                    self.guardian_id_counter += 1

                else:  # 5% single father families
                    # Single father
                    fake = Faker()
                    father = {
                        "guardian_id": self.guardian_id_counter,
                        "first_name": fake.first_name_male(),
                        "last_name": student_last_name,
                        "email": fake.email(),
                        "phone": fake.phone_number(),
                    }
                    new_guardians.append(father)
                    self.guardians[self.guardian_id_counter] = father

                    father_relationship = {
                        "student_id": student_id,
                        "guardian_id": self.guardian_id_counter,
                        "guardian_type_id": 2,  # Father
                        "family_id": family_id,
                    }
                    new_student_guardians.append(father_relationship)
                    self.student_guardians[student_id] = father_relationship
                    self.guardian_id_counter += 1

            else:
                # Non-parent guardian (35% of remaining)
                guardian_types = [
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                ]  # Grandparents, aunt, uncle, legal guardian, other
                guardian_type_id = random.choice(guardian_types)
                fake = Faker()

                # Generate gender based on guardian type
                if guardian_type_id in [5, 7]:  # Grandmother, Aunt
                    first_name = fake.first_name_female()
                elif guardian_type_id in [6, 8]:  # Grandfather, Uncle
                    first_name = fake.first_name_male()
                else:
                    first_name = fake.first_name()

                guardian = {
                    "guardian_id": self.guardian_id_counter,
                    "first_name": first_name,
                    "last_name": fake.last_name(),  # Different last name
                    "email": fake.email(),
                    "phone": fake.phone_number(),
                }
                new_guardians.append(guardian)
                self.guardians[self.guardian_id_counter] = guardian

                guardian_relationship = {
                    "student_id": student_id,
                    "guardian_id": self.guardian_id_counter,
                    "guardian_type_id": guardian_type_id,
                    "family_id": family_id,
                }
                new_student_guardians.append(guardian_relationship)
                self.student_guardians[student_id] = guardian_relationship
                self.guardian_id_counter += 1

        if new_guardians:
            logger.info(
                f"Generated {len(new_guardians)} new guardians with {len(new_student_guardians)} relationships"
            )

        return new_guardians, new_student_guardians


class CurriculumManager:
    """Manages curriculum evolution and course offerings"""

    def __init__(self):
        self.active_subjects = {}
        self.historical_subjects = {}
        self.subject_id_counter = 1

    def load_baseline_subjects(self, subjects_df):
        """Load 2015-2016 subjects as baseline"""
        for _, subject in subjects_df.iterrows():
            self.active_subjects[subject["subject_id"]] = {
                "subject_id": subject["subject_id"],
                "name": subject["name"],
                "department_id": subject.get(
                    " department_id", subject.get("department_id", 1)
                ),  # Handle both with/without space
                "introduced_year": 2015,
                "is_core": subject["name"]
                in ["Mathematics", "English", "Science", "Social Studies"],
            }
            self.subject_id_counter = max(
                self.subject_id_counter, subject["subject_id"] + 1
            )

    def evolve_curriculum(self, year):
        """Apply curriculum changes for specific year"""
        changes = []

        # Year-specific curriculum updates
        if year == 2016:
            changes.extend(
                [
                    self._add_subject(
                        "Digital Literacy", 7, "Technology integration begins"
                    ),
                    self._modify_subject(
                        "Old World History", "World History", "Curriculum consolidation"
                    ),
                ]
            )
        elif year == 2017:
            changes.extend(
                [
                    self._add_subject("AP Calculus", 1, "Advanced mathematics option"),
                    self._add_subject("Environmental Science", 2, "STEM expansion"),
                ]
            )
        elif year == 2019:
            changes.extend(
                [
                    self._add_subject("Robotics", 7, "STEM Academy launch"),
                    self._add_subject("Mandarin Chinese", 8, "Language diversity"),
                ]
            )
        elif year == 2022:
            changes.extend(
                [
                    self._add_subject("Cybersecurity", 7, "Modern technology focus"),
                    self._add_subject("Data Science", 1, "21st century mathematics"),
                ]
            )
        elif year == 2023:
            changes.extend(
                [
                    self._add_subject(
                        "International Baccalaureate", 9, "Global curriculum"
                    ),
                    self._add_subject("Dual Enrollment Math", 1, "College partnership"),
                ]
            )

        if changes:
            logger.info(f"Year {year}: Applied {len(changes)} curriculum changes")

        return changes

    def _add_subject(self, name, department_id, reason):
        """Add new subject to curriculum"""
        subject = {
            "subject_id": self.subject_id_counter,
            "name": name,
            "department_id": department_id,
            "introduced_year": datetime.now().year,
            "is_core": False,
        }

        self.active_subjects[self.subject_id_counter] = subject
        self.subject_id_counter += 1

        return f"Added: {name} ({reason})"

    def _modify_subject(self, old_name, new_name, reason):
        """Modify existing subject"""
        for subject in self.active_subjects.values():
            if subject["name"] == old_name:
                subject["name"] = new_name
                return f"Modified: {old_name} → {new_name} ({reason})"

        return f"Could not find subject: {old_name}"


class LuminosityDecadeGenerator:
    """Main class for generating 10 years of school data"""

    def __init__(self, baseline_year=2015, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)

        self.baseline_year = baseline_year
        self.student_registry = StudentRegistry()
        self.teacher_registry = TeacherRegistry()
        self.curriculum_manager = CurriculumManager()
        self.guardian_registry = GuardianRegistry()

        # Load year-specific configurations
        self.year_configs = self._load_year_configurations()

    def _load_year_configurations(self):
        """Define configuration for each year of expansion"""
        return {
            2016: SchoolYearConfig(
                year=2016,
                enrollment_target=505,
                graduation_count=38,
                new_kindergarten_count=42,
                teacher_turnover_rate=0.08,
                curriculum_changes=["Digital Literacy", "World History merge"],
                major_events=["Technology initiative launch"],
                technology_updates=["Tablet program pilot"],
                fee_adjustments={"Technology Fee": 1.10},
            ),
            2017: SchoolYearConfig(
                year=2017,
                enrollment_target=510,
                graduation_count=41,
                new_kindergarten_count=39,
                teacher_turnover_rate=0.07,
                curriculum_changes=["AP Calculus", "Environmental Science"],
                major_events=["New science lab", "Department head changes"],
                technology_updates=["WiFi infrastructure upgrade"],
                fee_adjustments={},
            ),
            2018: SchoolYearConfig(
                year=2018,
                enrollment_target=515,
                graduation_count=37,
                new_kindergarten_count=44,
                teacher_turnover_rate=0.09,
                curriculum_changes=["STEM focus expansion"],
                major_events=["Growing neighborhood enrollment"],
                technology_updates=["Tablet program expansion"],
                fee_adjustments={},
            ),
            2019: SchoolYearConfig(
                year=2019,
                enrollment_target=525,
                graduation_count=39,
                new_kindergarten_count=48,
                teacher_turnover_rate=0.06,
                curriculum_changes=["STEM Academy", "Robotics", "Mandarin"],
                major_events=["Facility expansion", "New classrooms"],
                technology_updates=["1:1 tablet deployment"],
                fee_adjustments={"Technology Fee": 1.25},
            ),
            2020: SchoolYearConfig(
                year=2020,
                enrollment_target=495,  # COVID impact
                graduation_count=42,
                new_kindergarten_count=35,
                teacher_turnover_rate=0.12,
                curriculum_changes=["Remote learning adaptations"],
                major_events=["COVID-19 pandemic", "Hybrid learning model"],
                technology_updates=["Remote learning platform"],
                fee_adjustments={"Technology Fee": 1.50},
            ),
            2021: SchoolYearConfig(
                year=2021,
                enrollment_target=540,  # Recovery
                graduation_count=35,
                new_kindergarten_count=52,
                teacher_turnover_rate=0.08,
                curriculum_changes=["Social-emotional learning", "Learning recovery"],
                major_events=["Return to in-person", "Academic support programs"],
                technology_updates=["Health screening systems"],
                fee_adjustments={},
            ),
            2022: SchoolYearConfig(
                year=2022,
                enrollment_target=555,
                graduation_count=45,
                new_kindergarten_count=48,
                teacher_turnover_rate=0.07,
                curriculum_changes=["Cybersecurity", "Data Science"],
                major_events=[
                    "Teacher professional development",
                    "New evaluation system",
                ],
                technology_updates=["Laptop replacement program"],
                fee_adjustments={
                    "Technology Fee": 1.30,
                    "Tuition": 1.10,
                },  # 10% tuition increase
            ),
            2023: SchoolYearConfig(
                year=2023,
                enrollment_target=570,
                graduation_count=47,
                new_kindergarten_count=49,
                teacher_turnover_rate=0.06,
                curriculum_changes=["International Baccalaureate", "Dual enrollment"],
                major_events=["Academic excellence initiative", "College partnerships"],
                technology_updates=["Learning management system"],
                fee_adjustments={"Tuition": 1.05},
            ),
            2024: SchoolYearConfig(
                year=2024,
                enrollment_target=580,
                graduation_count=48,
                new_kindergarten_count=50,
                teacher_turnover_rate=0.05,
                curriculum_changes=["Advanced placement expansion"],
                major_events=["Science lab renovation", "Library modernization"],
                technology_updates=["AI tutoring pilot"],
                fee_adjustments={},
            ),
            2025: SchoolYearConfig(
                year=2025,
                enrollment_target=585,
                graduation_count=50,
                new_kindergarten_count=51,
                teacher_turnover_rate=0.05,
                curriculum_changes=["Global citizenship program"],
                major_events=["10-year anniversary", "Alumni network launch"],
                technology_updates=["Next-gen learning tools"],
                fee_adjustments={"Tuition": 1.03},
            ),
        }

    def load_baseline_data(self, data_directory):
        """Load 2015-2016 baseline data from CSV files"""
        logger.info("Loading baseline data from 2015-2016...")

        students_df = pd.read_csv(os.path.join(data_directory, "students.csv"))
        teachers_df = pd.read_csv(os.path.join(data_directory, "teachers.csv"))
        subjects_df = pd.read_csv(os.path.join(data_directory, "subjects.csv"))

        self.student_registry.load_baseline_students(students_df)
        self.teacher_registry.load_baseline_teachers(teachers_df)
        self.curriculum_manager.load_baseline_subjects(subjects_df)

        logger.info(
            f"Loaded {len(students_df)} students, {len(teachers_df)} teachers, {len(subjects_df)} subjects"
        )

    def generate_school_year(self, year):
        """Generate complete data for a specific school year"""
        logger.info(f"\n{'='*50}")
        logger.info(f"GENERATING SCHOOL YEAR {year}-{year+1}")
        logger.info(f"{'='*50}")

        config = self.year_configs[year]
        year_data = {}

        # 1. Process student transitions
        graduated, advanced = self.student_registry.advance_grade_levels(year)
        new_k = self.student_registry.enroll_new_kindergarteners(
            year, config.new_kindergarten_count
        )
        transfers_in, transfers_out = self.student_registry.process_transfers(
            year, random.randint(3, 8), random.randint(2, 7), self.guardian_registry
        )

        # 2. Process teacher changes
        retirements, resignations, new_hires = (
            self.teacher_registry.process_annual_changes(
                year,
                target_teacher_count=62,  # Slight growth
                turnover_rate=config.teacher_turnover_rate,
            )
        )

        # 3. Apply curriculum changes
        curriculum_changes = self.curriculum_manager.evolve_curriculum(year)

        # 4. Generate static reference data (same every year but needed)
        year_data["school_metadata"] = self._create_school_metadata()
        year_data["departments"] = self._create_departments()
        year_data["grade_levels"] = self._create_grade_levels()
        year_data["guardian_types"] = self._create_guardian_types()
        year_data["fee_types"] = self._create_fee_types()
        year_data["periods"] = self._create_periods()
        year_data["classrooms"] = self._create_classrooms()

        # 5. Generate people and relationships
        year_data["students"] = self._create_students_dataframe()
        year_data["teachers"] = self._create_teachers_dataframe()
        year_data["subjects"] = self._create_subjects_dataframe()

        # Generate guardians for current students
        current_students = list(self.student_registry.active_students.values())
        new_guardians, new_student_guardians = (
            self.guardian_registry.generate_guardians_for_students(current_students)
        )
        year_data["guardians"] = pd.DataFrame(
            list(self.guardian_registry.guardians.values())
        )
        year_data["student_guardians"] = pd.DataFrame(
            list(self.guardian_registry.student_guardians.values())
        )

        # 6. Generate academic data
        year_data["classes"] = self._generate_classes(year)
        year_data["enrollments"] = self._generate_enrollments(year_data["classes"])
        year_data["teacher_subjects"] = self._generate_teacher_subjects()
        year_data["assignments"] = self._generate_assignments(
            year, year_data["classes"]
        )
        year_data["grades"] = self._generate_grades(
            year, year_data["assignments"], year_data["enrollments"]
        )
        year_data["attendance"] = self._generate_attendance(year)

        # 7. Generate administrative data
        year_data["discipline_reports"] = self._generate_discipline_reports(year)
        year_data["standardized_tests"] = self._generate_standardized_tests(year)
        year_data["student_grade_history"] = self._generate_student_grade_history(year)
        year_data["payments"] = self._generate_payments(year)

        # 8. Generate supporting data
        year_data["school_years"] = self._create_school_year_record(year)
        year_data["terms"] = self._create_terms_records(year)
        year_data["school_calendar"] = self._generate_school_calendar(year)

        # 9. Create summary report
        summary = self._create_year_summary(
            year,
            config,
            graduated,
            new_k,
            transfers_in,
            transfers_out,
            retirements,
            resignations,
            new_hires,
            curriculum_changes,
        )

        logger.info("\nYear Summary:")
        logger.info(f"  Total Students: {len(year_data['students'])}")
        logger.info(f"  Total Teachers: {len(year_data['teachers'])}")
        logger.info(f"  Total Classes: {len(year_data['classes'])}")
        logger.info(f"  Total Guardians: {len(year_data['guardians'])}")
        logger.info(f"  Graduated: {len(graduated)}")
        logger.info(f"  New Kindergarten: {len(new_k)}")

        return year_data, summary

    def generate_decade(
        self, start_year=2016, end_year=2025, output_directory="../data/decade"
    ):
        """Generate complete 10-year dataset"""
        logger.info(f"Starting 10-year generation: {start_year}-{end_year}")

        os.makedirs(output_directory, exist_ok=True)
        decade_summary = {}

        for year in range(start_year, end_year + 1):
            year_data, summary = self.generate_school_year(year)

            # Save year data
            year_dir = os.path.join(output_directory, f"{year}-{year+1}")
            os.makedirs(year_dir, exist_ok=True)

            for table_name, df in year_data.items():
                filepath = os.path.join(year_dir, f"{table_name}.csv")
                df.to_csv(filepath, index=False)

            # Save summary
            summary_file = os.path.join(year_dir, "year_summary.json")
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)

            decade_summary[year] = summary

            logger.info(f"Completed {year}-{year+1} school year")

        # Save decade summary
        decade_summary_file = os.path.join(output_directory, "decade_summary.json")
        with open(decade_summary_file, "w") as f:
            json.dump(decade_summary, f, indent=2)

        logger.info(f"\n🎓 DECADE GENERATION COMPLETE! 🎓")
        logger.info(f"Data saved to: {output_directory}")

        return decade_summary

    # ==================== REFERENCE DATA CREATORS ====================

    def _create_school_metadata(self):
        """Create school metadata table"""
        return pd.DataFrame(
            [
                {
                    "school_name": "Luminosity Academy",
                    "address": "123 Education Drive",
                    "city": "Bangor",
                    "state": "Maine",
                    "zip": "04401",
                    "phone": "(207) 555-0123",
                    "email": "info@luminosityacademy.edu",
                    "principal": "Dr. Sarah Johnson",
                }
            ]
        )

    def _create_departments(self):
        """Create departments table"""
        return pd.DataFrame(
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

    def _create_grade_levels(self):
        """Create grade levels table"""
        return pd.DataFrame(
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

    def _create_guardian_types(self):
        """Create guardian types table"""
        return pd.DataFrame(
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

    def _create_fee_types(self):
        """Create fee types table"""
        return pd.DataFrame(
            [
                {
                    "fee_type_id": 1,
                    "name": "Tech Fee",
                    "amount": 100,
                    "frequency": "One Time",
                },
                {
                    "fee_type_id": 2,
                    "name": "Field Trip Fund",
                    "amount": 50,
                    "frequency": "One Time",
                },
                {
                    "fee_type_id": 3,
                    "name": "Lunch Plan",
                    "amount": 400,
                    "frequency": "Monthly",
                },
                {
                    "fee_type_id": 4,
                    "name": "Tuition",
                    "amount": 8000,
                    "frequency": "Annual",
                },
                {
                    "fee_type_id": 5,
                    "name": "Activity Fee",
                    "amount": 75,
                    "frequency": "Per Term",
                },
            ]
        )

    def _create_periods(self):
        """Create periods table"""
        return pd.DataFrame(
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

    def _create_classrooms(self):
        """Create classrooms table"""
        return pd.DataFrame(
            [
                {
                    "classroom_id": i,
                    "room_number": f"Room {100+i}",
                    "capacity": random.randint(20, 30),
                }
                for i in range(1, 21)
            ]
        )

    # ==================== ENTITY DATA CREATORS ====================

    def _create_students_dataframe(self):
        """Convert student registry to DataFrame"""
        students = []
        for student in self.student_registry.active_students.values():
            students.append(
                {
                    "student_id": student["student_id"],
                    "first_name": student["first_name"],
                    "last_name": student["last_name"],
                    "gender": student["gender"],
                    "date_of_birth": student["date_of_birth"],
                    "grade_level_id": student["grade_level_id"],
                }
            )
        return pd.DataFrame(students)

    def _create_teachers_dataframe(self):
        """Convert teacher registry to DataFrame"""
        teachers = []
        for teacher in self.teacher_registry.active_teachers.values():
            teachers.append(
                {
                    "teacher_id": teacher["teacher_id"],
                    "first_name": teacher["first_name"],
                    "last_name": teacher["last_name"],
                    "department_id": teacher["department_id"],
                }
            )
        return pd.DataFrame(teachers)

    def _create_subjects_dataframe(self):
        """Convert subjects to DataFrame"""
        subjects = []
        for subject in self.curriculum_manager.active_subjects.values():
            subjects.append(
                {
                    "subject_id": subject["subject_id"],
                    "name": subject["name"],
                    "department_id": subject["department_id"],
                }
            )
        return pd.DataFrame(subjects)

    def _generate_teacher_subjects(self):
        """Generate teacher-subject assignments"""
        teacher_subjects = []
        for teacher in self.teacher_registry.active_teachers.values():
            teacher_id = teacher["teacher_id"]
            department_id = teacher["department_id"]

            # Find subjects in teacher's department
            dept_subjects = [
                s
                for s in self.curriculum_manager.active_subjects.values()
                if s["department_id"] == department_id
            ]

            # Assign 1-3 subjects per teacher
            num_subjects = min(random.randint(1, 3), len(dept_subjects))
            if num_subjects > 0:
                assigned_subjects = random.sample(dept_subjects, num_subjects)

                for subject in assigned_subjects:
                    teacher_subjects.append(
                        {
                            "teacher_id": teacher_id,
                            "subject_id": subject["subject_id"],
                            "department_id": department_id,
                        }
                    )

        return pd.DataFrame(teacher_subjects)

    # ==================== ACADEMIC DATA GENERATORS ====================

    def _generate_classes(self, year):
        """Generate class sections for the year"""
        classes = []
        class_id = 1

        # Generate classes based on current enrollment and grade levels
        grade_distribution = {}
        for student in self.student_registry.active_students.values():
            grade = student["grade_level_id"]
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        for grade_level, student_count in grade_distribution.items():
            sections_needed = max(1, student_count // 25)  # ~25 students per section

            # Subject mapping by grade level (following Document of Truth)
            if grade_level <= 6:  # Elementary (K-5)
                subjects = [
                    "Homeroom",
                    "Mathematics",
                    "Reading",
                    "Science",
                    "Social Studies",
                ]
            elif grade_level <= 9:  # Middle (6-8)
                subjects = [
                    "Mathematics",
                    "English Language Arts",
                    "Science",
                    "Social Studies",
                    "Art",
                    "Physical Education",
                    "Technology",
                ]
            elif grade_level == 10:  # 9th grade
                subjects = [
                    "Algebra I",
                    "Biology",
                    "Physical Education",
                    "English",
                    "Geography",
                    "Spanish I",
                    "Computer Science",
                ]
            elif grade_level == 11:  # 10th grade
                subjects = [
                    "Geometry",
                    "Life Science",
                    "Physical Education",
                    "American Literature",
                    "Old World History",
                    "Spanish II",
                    "Visual Arts",
                ]
            elif grade_level == 12:  # 11th grade
                subjects = [
                    "Algebra II",
                    "Chemistry",
                    "Physical Education",
                    "English Literature",
                    "New World History",
                    "Leadership",
                    "Music Performance",
                ]
            else:  # 12th grade
                subjects = [
                    "Calculus",
                    "Psychology",
                    "Physical Education",
                    "World Literature",
                    "Government/Economics",
                ]

            for section in range(sections_needed):
                for period, subject in enumerate(subjects, 1):
                    # Find appropriate teacher
                    available_teachers = list(
                        self.teacher_registry.active_teachers.keys()
                    )
                    if available_teachers:
                        teacher_id = random.choice(available_teachers)
                    else:
                        teacher_id = 1  # Fallback

                    classes.append(
                        {
                            "class_id": class_id,
                            "name": subject,
                            "grade_level_id": grade_level,
                            "teacher_id": teacher_id,
                            "classroom_id": random.randint(1, 20),
                            "period_id": period,
                            "term_id": random.randint(1, 4),
                        }
                    )
                    class_id += 1

        return pd.DataFrame(classes)

    def _generate_enrollments(self, classes_df):
        """Generate student enrollments in classes"""
        enrollments = []
        enrollment_id = 1

        for _, class_record in classes_df.iterrows():
            grade_level = class_record["grade_level_id"]

            # Find students in this grade level
            grade_students = [
                s
                for s in self.student_registry.active_students.values()
                if s["grade_level_id"] == grade_level
            ]

            # Enroll students in class
            for student in grade_students:
                enrollments.append(
                    {
                        "enrollment_id": f"ENR{enrollment_id:06d}",
                        "student_id": student["student_id"],
                        "class_id": class_record["class_id"],
                    }
                )
                enrollment_id += 1

        return pd.DataFrame(enrollments)

    def _generate_assignments(self, year, classes_df):
        """Generate assignments for all classes (~2 per week per class)"""
        assignments = []
        assignment_id = 1

        for _, class_record in classes_df.iterrows():
            # Calculate assignments based on ~2 per week for 36 weeks
            assignments_per_class = random.randint(65, 75)  # ~70 assignments per year

            for i in range(assignments_per_class):
                category = random.choice(
                    ["Homework", "Quiz", "Test", "Project", "Participation"]
                )

                # Points mapping
                points_mapping = {
                    "Homework": random.randint(10, 25),
                    "Quiz": random.randint(25, 50),
                    "Test": random.randint(75, 100),
                    "Project": random.randint(50, 100),
                    "Participation": random.randint(5, 15),
                }
                points = points_mapping[category]

                # Generate due date within school year
                start_date = date(year, 8, 26)
                end_date = date(year + 1, 6, 6)
                due_date = self.fake.date_between(start_date, end_date)

                assignments.append(
                    {
                        "assignment_id": assignment_id,
                        "class_id": class_record["class_id"],
                        "title": f"{category} {i+1}",
                        "due_date": due_date.strftime("%Y-%m-%d"),
                        "points_possible": points,
                        "category": category,
                        "term_id": random.randint(1, 4),
                    }
                )
                assignment_id += 1

        return pd.DataFrame(assignments)

    def _generate_grades(self, year, assignments_df, enrollments_df):
        """Generate grades following 70-100 range with 85-90 median"""
        grades = []
        grade_id = 1

        for _, assignment in assignments_df.iterrows():
            class_id = assignment["class_id"]

            # Find students enrolled in this class
            enrolled_students = enrollments_df[enrollments_df["class_id"] == class_id][
                "student_id"
            ].tolist()

            for student_id in enrolled_students:
                score = self._generate_realistic_grade(assignment["points_possible"])

                grades.append(
                    {
                        "grade_id": grade_id,
                        "student_id": student_id,
                        "assignment_id": assignment["assignment_id"],
                        "score": score,
                        "submitted_on": assignment["due_date"],
                        "term_id": assignment["term_id"],
                    }
                )
                grade_id += 1

        return pd.DataFrame(grades)

    def _generate_realistic_grade(self, points_possible):
        """Generate realistic grade distribution per Document of Truth"""
        rand = random.random()

        if rand < 0.03:  # 3% perfect grades
            percentage = random.uniform(0.95, 1.0)
        elif rand < 0.08:  # 3-5% failing grades
            percentage = random.uniform(0.0, 0.69)
        else:  # Most students in 70-100 range with 85-90 median
            percentage = np.random.normal(0.87, 0.08)  # 87% median
            percentage = max(0.70, min(1.0, percentage))

        return max(0, min(points_possible, round(points_possible * percentage)))

    def _generate_attendance(self, year):
        """Generate attendance following 5% absence, 3% tardy policy"""
        attendance = []
        attendance_id = 1

        school_days = self._get_school_days(year)

        for student in self.student_registry.active_students.values():
            student_id = student["student_id"]

            # Calculate absence and tardy patterns per Document of Truth
            total_days = len(school_days)
            absence_count = int(total_days * 0.05)  # 5% absence rate
            tardy_count = int(total_days * 0.03)  # 3% tardy rate

            absence_days = random.sample(
                school_days, min(absence_count, len(school_days))
            )
            remaining_days = [day for day in school_days if day not in absence_days]
            tardy_days = random.sample(
                remaining_days, min(tardy_count, len(remaining_days))
            )

            for day in school_days:
                if day in absence_days:
                    status = random.choice(["Absent", "Excused"])
                elif day in tardy_days:
                    status = "Tardy"
                else:
                    status = "Present"

                attendance.append(
                    {
                        "attendance_id": f"ATT{attendance_id:06d}",
                        "student_id": student_id,
                        "date": day,
                        "status": status,
                    }
                )
                attendance_id += 1

        return pd.DataFrame(attendance)

    # ==================== ADMINISTRATIVE DATA GENERATORS ====================

    def _generate_discipline_reports(self, year):
        """Generate discipline reports for students"""
        discipline_reports = []
        report_id = 1

        # Generate reports for ~5% of students per year
        students = list(self.student_registry.active_students.values())
        students_with_incidents = random.sample(students, int(len(students) * 0.05))

        for student in students_with_incidents:
            # 1-3 incidents per student
            incident_count = random.randint(1, 3)

            for _ in range(incident_count):
                incident_date = self.fake.date_between(
                    start_date=date(year, 8, 26), end_date=date(year + 1, 6, 6)
                )

                severity = random.choices(
                    ["Minor", "Major", "Severe"], weights=[70, 25, 5]
                )[0]

                incident_type = random.choice(
                    [
                        "Tardiness",
                        "Disruption",
                        "Disrespect",
                        "Fighting",
                        "Vandalism",
                        "Academic Dishonesty",
                        "Other",
                    ]
                )

                actions = {
                    "Minor": ["Verbal Warning", "Parent Contact", "Detention"],
                    "Major": [
                        "Office Referral",
                        "Parent Conference",
                        "In-School Suspension",
                    ],
                    "Severe": [
                        "Out-of-School Suspension",
                        "Parent Conference",
                        "Behavior Plan",
                    ],
                }

                action_taken = random.choice(actions[severity])

                discipline_reports.append(
                    {
                        "discipline_report_id": f"DISC{report_id:06d}",
                        "student_id": student["student_id"],
                        "date": incident_date.strftime("%Y-%m-%d"),
                        "severity": severity,
                        "type": incident_type,
                        "action_taken": action_taken,
                    }
                )
                report_id += 1

        return pd.DataFrame(discipline_reports)

    def _generate_standardized_tests(self, year):
        """Generate standardized test results"""
        standardized_tests = []
        test_id = 1

        # Test all students based on grade level
        for student in self.student_registry.active_students.values():
            grade_level = student["grade_level_id"]

            # Determine appropriate tests by grade
            tests = []
            if grade_level >= 3:  # State testing starts in 3rd grade
                tests.append("State Math Assessment")
                tests.append("State Reading Assessment")
            if grade_level >= 10:  # High school tests
                tests.extend(["PSAT", "SAT"])
            if grade_level >= 11:  # Advanced students
                if random.random() < 0.3:  # 30% take AP tests
                    tests.append("AP Exam")

            for test_name in tests:
                test_date = self.fake.date_between(
                    start_date=date(year, 3, 1),
                    end_date=date(year, 5, 31),  # Testing season
                )

                # Generate realistic scores based on student performance
                if "SAT" in test_name:
                    score = random.randint(400, 1600)
                    percentile = min(99, max(1, int((score - 400) / 12)))
                elif "PSAT" in test_name:
                    score = random.randint(320, 1520)
                    percentile = min(99, max(1, int((score - 320) / 12)))
                else:
                    score = random.randint(150, 300)
                    percentile = random.randint(1, 99)

                subject = "Mathematics" if "Math" in test_name else "Reading"

                standardized_tests.append(
                    {
                        "test_id": f"TEST{test_id:06d}",
                        "student_id": student["student_id"],
                        "test_name": test_name,
                        "test_date": test_date.strftime("%Y-%m-%d"),
                        "score": score,
                        "subject": subject,
                        "percentile": percentile,
                    }
                )
                test_id += 1

        return pd.DataFrame(standardized_tests)

    def _generate_student_grade_history(self, year):
        """Generate year-end academic summaries"""
        student_grade_history = []
        history_id = 1

        for student in self.student_registry.active_students.values():
            # Calculate realistic GPA (0.0-4.0 scale)
            rand = random.random()
            if rand < 0.03:  # 3% perfect students
                gpa = random.uniform(3.8, 4.0)
            elif rand < 0.08:  # 5% struggling students
                gpa = random.uniform(1.5, 2.5)
            else:  # Most students
                gpa = np.random.normal(3.2, 0.4)  # 3.2 average
                gpa = max(0.0, min(4.0, gpa))

            student_grade_history.append(
                {
                    "student_grade_history_id": f"HIST{history_id:06d}",
                    "student_id": student["student_id"],
                    "school_year_id": year - 2014,  # Convert to school year ID
                    "gpa": round(gpa, 3),
                    "grade_level_id": student["grade_level_id"],
                }
            )
            history_id += 1

        return pd.DataFrame(student_grade_history)

    def _generate_payments(self, year):
        """Generate payment records for guardians"""
        payments = []
        payment_id = 1

        # Generate payments for each family
        families_processed = set()

        for student_guardian in self.guardian_registry.student_guardians.values():
            family_id = student_guardian.get("family_id")
            if family_id in families_processed:
                continue
            families_processed.add(family_id)

            guardian_id = student_guardian["guardian_id"]

            # Each family pays tuition (required)
            tuition_amount = 8000
            payment_plan = random.choices(
                ["annual", "9_month", "12_month"],
                weights=[10, 70, 20],  # 10% annual, 70% 9-month, 20% 12-month
            )[0]

            if payment_plan == "annual":
                # Single payment in August
                payments.append(
                    {
                        "payment_id": f"PAY{payment_id:06d}",
                        "guardian_id": guardian_id,
                        "fee_type_id": 4,  # Tuition
                        "amount_paid": tuition_amount,
                        "payment_date": f"{year}-08-15",
                    }
                )
                payment_id += 1
            elif payment_plan == "9_month":
                # 9 monthly payments
                monthly_amount = tuition_amount / 9
                for month in range(9):
                    if month < 5:  # Aug-Dec of current year (months 0-4 = Aug-Dec)
                        payment_month = 8 + month
                        payment_year = year
                    else:  # Jan-May of next year (months 5-8 = Jan-May)
                        payment_month = month - 4  # 5-4=1(Jan), 6-4=2(Feb), etc.
                        payment_year = year + 1

                    payment_date = date(payment_year, payment_month, 15)
                    payments.append(
                        {
                            "payment_id": f"PAY{payment_id:06d}",
                            "guardian_id": guardian_id,
                            "fee_type_id": 4,  # Tuition
                            "amount_paid": int(monthly_amount),
                            "payment_date": payment_date.strftime("%Y-%m-%d"),
                        }
                    )
                    payment_id += 1
            else:  # 12_month
                # 12 monthly payments
                monthly_amount = tuition_amount / 12
                for month in range(12):
                    if month < 5:  # Aug-Dec of current year (months 0-4 = Aug-Dec)
                        payment_month = 8 + month
                        payment_year = year
                    else:  # Jan-Jul of next year (months 5-11 = Jan-Jul)
                        payment_month = month - 4  # 5-4=1(Jan), 6-4=2(Feb), etc.
                        payment_year = year + 1

                    payment_date = date(payment_year, payment_month, 15)
                    payments.append(
                        {
                            "payment_id": f"PAY{payment_id:06d}",
                            "guardian_id": guardian_id,
                            "fee_type_id": 4,  # Tuition
                            "amount_paid": int(monthly_amount),
                            "payment_date": payment_date.strftime("%Y-%m-%d"),
                        }
                    )
                    payment_id += 1

            # Other fees (tech fee, field trip, etc.)
            other_fees = [
                (1, 100),  # Tech Fee
                (2, 50),  # Field Trip Fund
            ]

            for fee_type_id, amount in other_fees:
                if random.random() < 0.8:  # 80% pay optional fees
                    payments.append(
                        {
                            "payment_id": f"PAY{payment_id:06d}",
                            "guardian_id": guardian_id,
                            "fee_type_id": fee_type_id,
                            "amount_paid": amount,
                            "payment_date": f"{year}-08-{random.randint(10, 30)}",
                        }
                    )
                    payment_id += 1

        return pd.DataFrame(payments)

    # ==================== SUPPORTING DATA GENERATORS ====================

    def _get_school_days(self, year):
        """Get list of school days for the year (180 days total)"""
        start_date = date(year, 8, 26)
        end_date = date(year + 1, 6, 6)

        school_days = []
        current_date = start_date

        while current_date <= end_date and len(school_days) < 180:
            # Skip weekends and holidays
            if current_date.weekday() < 5:  # Monday-Friday
                if not self._is_holiday(current_date):
                    school_days.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

        return school_days

    def _is_holiday(self, check_date):
        """Check if date is a holiday"""
        holiday_periods = [
            (
                date(check_date.year, 11, 25),
                date(check_date.year, 11, 29),
            ),  # Thanksgiving week
            (
                date(check_date.year, 12, 23),
                date(check_date.year + 1, 1, 3),
            ),  # Winter break
            (
                date(check_date.year + 1, 3, 15),
                date(check_date.year + 1, 3, 22),
            ),  # Spring break
        ]

        for start, end in holiday_periods:
            if start <= check_date <= end:
                return True
        return False

    def _generate_school_calendar(self, year):
        """Generate school calendar with holidays and breaks"""
        calendar_data = []
        start_date = date(year, 8, 26)
        end_date = date(year + 1, 6, 6)
        current_date = start_date

        # Define major holidays and breaks
        holidays = {
            date(year, 9, 2): "Labor Day",
            date(year, 10, 14): "Columbus Day",
            date(year, 11, 11): "Veterans Day",
            date(year, 11, 28): "Thanksgiving",
            date(year, 11, 29): "Thanksgiving Break",
            date(year + 1, 1, 20): "Martin Luther King Jr. Day",
            date(year + 1, 2, 17): "Presidents Day",
            date(year + 1, 5, 26): "Memorial Day",
        }

        # Define break periods
        breaks = [
            (date(year, 12, 23), date(year + 1, 1, 3), "Christmas Break"),
            (date(year + 1, 3, 17), date(year + 1, 3, 21), "Spring Break"),
        ]

        while current_date <= end_date:
            is_weekend = current_date.weekday() >= 5
            is_holiday = current_date in holidays
            is_break = any(start <= current_date <= end for start, end, _ in breaks)

            is_school_day = not (is_weekend or is_holiday or is_break)

            comment = ""
            holiday_name = ""
            day_type = "school_day"
            label = ""

            if is_weekend:
                day_type = "weekend"
                comment = "Weekend"
                label = "Weekend"
            elif is_holiday:
                day_type = "holiday"
                holiday_name = holidays[current_date]
                comment = holiday_name
                label = holiday_name
            elif is_break:
                day_type = "break"
                break_name = next(
                    name for start, end, name in breaks if start <= current_date <= end
                )
                comment = break_name
                label = break_name

            calendar_data.append(
                {
                    "calendar_date": current_date.strftime("%Y-%m-%d"),
                    "is_school_day": is_school_day,
                    "is_holiday": is_holiday,
                    "holiday_name": holiday_name,
                    "comment": comment,
                    "day_type": day_type,
                    "label": label,
                }
            )

            current_date += timedelta(days=1)

        return pd.DataFrame(calendar_data)

    def _create_school_year_record(self, year):
        """Create school year record"""
        return pd.DataFrame(
            [
                {
                    "school_year_id": year - 2014,  # Start from 1 for 2015
                    "start_date": f"{year}-08-26",
                    "end_date": f"{year+1}-06-06",
                }
            ]
        )

    def _create_terms_records(self, year):
        """Create term records for the year"""
        base_id = (year - 2015) * 4 + 1  # Ensure unique term IDs across years
        return pd.DataFrame(
            [
                {
                    "term_id": base_id,
                    "label": "Q1",
                    "start_date": f"{year}-08-26",
                    "end_date": f"{year}-10-25",
                    "school_year_id": year - 2014,
                },
                {
                    "term_id": base_id + 1,
                    "label": "Q2",
                    "start_date": f"{year}-10-28",
                    "end_date": f"{year}-12-20",
                    "school_year_id": year - 2014,
                },
                {
                    "term_id": base_id + 2,
                    "label": "Q3",
                    "start_date": f"{year+1}-01-06",
                    "end_date": f"{year+1}-03-14",
                    "school_year_id": year - 2014,
                },
                {
                    "term_id": base_id + 3,
                    "label": "Q4",
                    "start_date": f"{year+1}-03-17",
                    "end_date": f"{year+1}-06-06",
                    "school_year_id": year - 2014,
                },
            ]
        )

    def _create_year_summary(
        self,
        year,
        config,
        graduated,
        new_k,
        transfers_in,
        transfers_out,
        retirements,
        resignations,
        new_hires,
        curriculum_changes,
    ):
        """Create comprehensive year summary"""
        return {
            "year": year,
            "school_year_label": f"{year}-{year+1}",
            "enrollment_target": config.enrollment_target,
            "actual_enrollment": len(self.student_registry.active_students),
            "student_changes": {
                "graduated": len(graduated),
                "new_kindergarten": len(new_k),
                "transfers_in": len(transfers_in),
                "transfers_out": len(transfers_out),
            },
            "teacher_changes": {
                "retirements": len(retirements),
                "resignations": len(resignations),
                "new_hires": len(new_hires),
                "total_active": len(self.teacher_registry.active_teachers),
            },
            "curriculum_changes": curriculum_changes,
            "major_events": config.major_events,
            "technology_updates": config.technology_updates,
            "fee_adjustments": config.fee_adjustments,
        }


def _create_year_summary(
    self,
    year,
    config,
    graduated,
    new_k,
    transfers_in,
    transfers_out,
    retirements,
    resignations,
    new_hires,
    curriculum_changes,
):
    """Create comprehensive year summary"""
    return {
        "year": year,
        "school_year_label": f"{year}-{year+1}",
        "enrollment_target": config.enrollment_target,
        "actual_enrollment": len(self.student_registry.active_students),
        "student_changes": {
            "graduated": len(graduated),
            "new_kindergarten": len(new_k),
            "transfers_in": len(transfers_in),
            "transfers_out": len(transfers_out),
        },
        "teacher_changes": {
            "retirements": len(retirements),
            "resignations": len(resignations),
            "new_hires": len(new_hires),
            "total_active": len(self.teacher_registry.active_teachers),
        },
        "curriculum_changes": curriculum_changes,
        "major_events": config.major_events,
        "technology_updates": config.technology_updates,
        "fee_adjustments": config.fee_adjustments,
    }


# ==================== MAIN EXECUTION ====================


def main():
    """Main function to run the decade generator"""
    parser = argparse.ArgumentParser(
        description="Generate 10 years of Luminosity School historical data"
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=2016,
        help="Start year for generation (default: 2016)",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=2025,
        help="End year for generation (default: 2025)",
    )
    parser.add_argument(
        "--baseline-dir",
        default="./data/clean_csv",
        help="Directory containing baseline 2015-2016 data",
    )
    parser.add_argument(
        "--output-dir",
        default="./data/decade",
        help="Output directory for generated decade data",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.start_year > args.end_year:
        logger.error("Start year must be <= end year")
        return 1

    if not os.path.exists(args.baseline_dir):
        logger.error(f"Baseline directory does not exist: {args.baseline_dir}")
        return 1

    # Initialize generator
    logger.info("🚀 LUMINOSITY DECADE GENERATOR STARTING 🚀")
    logger.info(f"Generating data for years {args.start_year}-{args.end_year}")
    logger.info(f"Using seed: {args.seed}")

    generator = LuminosityDecadeGenerator(seed=args.seed)

    try:
        # Load baseline data
        generator.load_baseline_data(args.baseline_dir)

        # Generate decade of data
        decade_summary = generator.generate_decade(
            start_year=args.start_year,
            end_year=args.end_year,
            output_directory=args.output_dir,
        )

        # Print final summary
        total_students = sum(
            summary["actual_enrollment"] for summary in decade_summary.values()
        )
        total_years = len(decade_summary)

        logger.info("\n" + "=" * 60)
        logger.info("🎓 DECADE GENERATION COMPLETE! 🎓")
        logger.info("=" * 60)
        logger.info(f"Years generated: {total_years}")
        logger.info(f"Total student-years: {total_students}")
        logger.info(f"Output directory: {args.output_dir}")
        logger.info(f"Summary file: {args.output_dir}/decade_summary.json")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
