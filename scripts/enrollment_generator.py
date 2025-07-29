#!/usr/bin/env python3
"""
Luminosity Enrollment Generator - SIMPLE VERSION THAT WORKS
No overthinking. Just assigns existing students to existing classes.
"""

import argparse
import logging
import os
import random
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class SimpleEnrollmentGenerator:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.enrollment_counter = 1
        self._load_data()

    def _load_data(self):
        """Load the CSV files."""
        self.students = pd.read_csv(os.path.join(self.data_dir, "students.csv"))
        self.classes = pd.read_csv(os.path.join(self.data_dir, "classes.csv"))
        logger.info(
            f"Loaded {len(self.students)} students and {len(self.classes)} classes"
        )

    def generate_for_year(self, year):
        """Generate enrollments for one year."""
        # Get students and classes for this year
        year_students = self.students[self.students["school_year_id"] == year]
        year_classes = self.classes[self.classes["school_year_id"] == year]

        logger.info(
            f"Year {year}: {len(year_students)} students, {len(year_classes)} classes"
        )

        enrollments = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # For each student, assign them to classes for their grade
        for _, student in year_students.iterrows():
            student_id = student["student_id"]
            grade = student["grade_level_id"]

            # Get all classes for this student's grade and year
            student_classes = year_classes[year_classes["grade_level_id"] == grade]

            # If no classes for exact grade, try adjacent grades
            if len(student_classes) < 4:
                for adj_grade in [grade - 1, grade + 1, grade - 2, grade + 2]:
                    if 0 <= adj_grade <= 12:
                        adj_classes = year_classes[
                            year_classes["grade_level_id"] == adj_grade
                        ]
                        student_classes = pd.concat([student_classes, adj_classes])
                        if len(student_classes) >= 4:
                            break

            # Take up to 6 classes for this student
            if len(student_classes) > 6:
                student_classes = student_classes.sample(n=6, random_state=42)

            # Create enrollment records
            for _, class_row in student_classes.iterrows():
                enrollments.append(
                    {
                        "enrollment_id": f"ENR{self.enrollment_counter:08d}",
                        "student_id": student_id,
                        "class_id": class_row["class_id"],
                        "school_year_id": year,
                        "created_at": timestamp,
                        "updated_at": timestamp,
                    }
                )
                self.enrollment_counter += 1

        return pd.DataFrame(enrollments)

    def generate_all_years(self):
        """Generate enrollments for all years 1-10."""
        all_enrollments = []

        for year in range(1, 11):
            year_enrollments = self.generate_for_year(year)
            all_enrollments.append(year_enrollments)
            logger.info(f"Year {year} complete: {len(year_enrollments)} enrollments")

        final = pd.concat(all_enrollments, ignore_index=True)
        logger.info(f"Total: {len(final)} enrollments")

        # Quick validation
        student_counts = final.groupby("student_id").size()
        single_enrollments = len(student_counts[student_counts == 1])
        logger.info(f"Students with single enrollments: {single_enrollments}")

        return final

    def save(self, enrollments, output_dir):
        """Save enrollments to CSV."""
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, "enrollments.csv")
        enrollments.to_csv(filepath, index=False)
        logger.info(f"Saved to {filepath}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default=r"C:\Users\Marshall Sisler\Projects\Luminosity\data\clean_csv",
    )
    parser.add_argument(
        "--output-dir",
        default=r"C:\Users\Marshall Sisler\Projects\Luminosity\data\clean_csv",
    )
    parser.add_argument("--school-year", type=int, help="Single year to generate")
    parser.add_argument("--batch", action="store_true", help="Generate all years")

    args = parser.parse_args()

    generator = SimpleEnrollmentGenerator(args.data_dir)

    if args.batch:
        enrollments = generator.generate_all_years()
    else:
        year = args.school_year or 1
        enrollments = generator.generate_for_year(year)

    generator.save(enrollments, args.output_dir)
    logger.info("Done!")


if __name__ == "__main__":
    main()
