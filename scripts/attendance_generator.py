#!/usr/bin/env python3
"""
Luminosity School Management System - Decade Attendance Generator
Generates realistic attendance patterns for all students across all school years (2016-2025)

Features:
- 10% absenteeism rate with seasonal patterns
- 20% tardiness rate (only when present)
- Realistic absence reasons with smart distribution
- Seasonal illness patterns (higher in winter)
- Family vacation patterns
- Weather-related absences
- No attendance records on non-school days
"""

import argparse
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AttendanceGenerator:
    def __init__(self, seed: int = 42):
        """Initialize attendance generator with specified random seed."""
        random.seed(seed)
        np.random.seed(seed)

        # Absence reasons with realistic distribution weights
        self.absence_reasons = {
            "Student illness": 0.35,  # Most common
            "Medical appointment": 0.15,
            "Medical or dental appointment": 0.12,
            "Family emergency": 0.08,
            "Transportation issues": 0.06,
            "A contagious sickness": 0.05,
            "Religious observance": 0.04,
            "Inclement weather": 0.04,
            "Death in immediate family": 0.02,
            "Medical": 0.03,
            "Quarantine": 0.03,
            "Suspension or expulsion from school": 0.02,
            "A sports events": 0.01,  # Least common
        }

        # Seasonal absence multipliers (higher in winter for illness)
        self.seasonal_patterns = {
            1: 1.4,  # January - flu season
            2: 1.35,  # February - flu season
            3: 1.1,  # March - spring allergies
            4: 0.9,  # April - good weather
            5: 0.8,  # May - good weather
            6: 0.7,  # June - end of year motivation
            7: 0.6,  # July - summer (minimal attendance)
            8: 0.8,  # August - back to school
            9: 0.9,  # September - fresh start
            10: 1.0,  # October - normal
            11: 1.1,  # November - weather changes
            12: 1.2,  # December - holiday season
        }

        # Family vacation periods (higher absence rates)
        self.vacation_periods = [
            (11, 22, 11, 29),  # Thanksgiving week
            (12, 20, 1, 8),  # Christmas/New Year
            (3, 15, 3, 22),  # Spring break periods
            (6, 1, 6, 15),  # Early summer
        ]

    def load_data(
        self, calendar_path: str, students_path: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load calendar and student data."""
        logger.info("Loading calendar and student data...")

        calendar_df = pd.read_csv(calendar_path)
        calendar_df["calendar_date"] = pd.to_datetime(calendar_df["calendar_date"])

        students_df = pd.read_csv(students_path)
        students_df["date_of_birth"] = pd.to_datetime(students_df["date_of_birth"])

        logger.info(
            f"Loaded {len(calendar_df)} calendar entries and {len(students_df)} student records"
        )
        return calendar_df, students_df

    def get_seasonal_multiplier(self, date: datetime) -> float:
        """Get seasonal absence multiplier for a given date."""
        month = date.month
        base_multiplier = self.seasonal_patterns.get(month, 1.0)

        # Check if date falls in vacation periods
        for start_month, start_day, end_month, end_day in self.vacation_periods:
            if self._date_in_range(date, start_month, start_day, end_month, end_day):
                base_multiplier *= 1.5  # 50% higher absence during vacation periods
                break

        return base_multiplier

    def _date_in_range(
        self,
        date: datetime,
        start_month: int,
        start_day: int,
        end_month: int,
        end_day: int,
    ) -> bool:
        """Check if date falls within a given month/day range."""
        if start_month <= end_month:
            # Same year range
            return (
                (date.month == start_month and date.day >= start_day)
                or (start_month < date.month < end_month)
                or (date.month == end_month and date.day <= end_day)
            )
        else:
            # Cross-year range (like Dec-Jan)
            return (
                (date.month == start_month and date.day >= start_day)
                or (date.month > start_month)
                or (date.month < end_month)
                or (date.month == end_month and date.day <= end_day)
            )

    def get_student_absence_probability(
        self, student_id: int, base_rate: float = 0.10
    ) -> float:
        """Get individual student absence probability with some variation."""
        # Use student_id as seed for consistent but varied absence patterns
        random.seed(student_id * 42)

        # Some students are naturally more absent than others
        individual_multiplier = random.uniform(0.3, 2.0)  # 30% to 200% of base rate

        # Reset to main seed
        random.seed(42)

        return min(
            base_rate * individual_multiplier, 0.35
        )  # Cap at 35% to avoid unrealistic rates

    def select_absence_reason(self, date: datetime, student_id: int) -> str:
        """Select appropriate absence reason based on date and patterns."""
        month = date.month

        # Adjust reason probabilities based on season
        adjusted_reasons = self.absence_reasons.copy()

        # Winter: more illness
        if month in [12, 1, 2]:
            adjusted_reasons["Student illness"] *= 1.5
            adjusted_reasons["A contagious sickness"] *= 2.0
            adjusted_reasons["Quarantine"] *= 2.0
            adjusted_reasons["Inclement weather"] *= 3.0

        # Spring: more medical appointments
        elif month in [3, 4, 5]:
            adjusted_reasons["Medical appointment"] *= 1.3
            adjusted_reasons["Medical or dental appointment"] *= 1.3

        # Holiday seasons: more family events
        elif month in [11, 12]:
            adjusted_reasons["Family emergency"] *= 1.2
            adjusted_reasons["Religious observance"] *= 1.5

        # Normalize probabilities
        total_weight = sum(adjusted_reasons.values())
        normalized_reasons = {k: v / total_weight for k, v in adjusted_reasons.items()}

        return random.choices(
            list(normalized_reasons.keys()), weights=list(normalized_reasons.values())
        )[0]

    def generate_student_yearly_attendance(
        self, student_id: int, school_year_id: int, school_days: List[datetime]
    ) -> List[Dict]:
        """Generate attendance records for one student for one school year."""
        attendance_records = []

        # Get student's individual absence rate
        base_absence_rate = self.get_student_absence_probability(student_id)

        # Calculate total expected absences for the year
        total_school_days = len(school_days)
        expected_absences = int(total_school_days * base_absence_rate)

        # Pre-determine absence days with seasonal weighting
        absence_weights = [self.get_seasonal_multiplier(day) for day in school_days]
        total_weight = sum(absence_weights)
        absence_probabilities = [w / total_weight for w in absence_weights]

        # Select absence days
        absence_indices = np.random.choice(
            len(school_days),
            size=min(expected_absences, len(school_days)),
            replace=False,
            p=absence_probabilities,
        )
        absence_days = set(absence_indices)

        # For remaining days (present), determine tardiness (20% of present days)
        present_indices = [i for i in range(len(school_days)) if i not in absence_days]
        tardy_count = int(len(present_indices) * 0.20)
        tardy_indices = set(
            random.sample(present_indices, min(tardy_count, len(present_indices)))
        )

        # Generate attendance records
        for i, school_day in enumerate(school_days):
            if i in absence_days:
                status = "Absent"
                notes = self.select_absence_reason(school_day, student_id)
            elif i in tardy_indices:
                status = "Tardy"
                notes = ""  # Tardies typically don't need detailed notes
            else:
                status = "Present"
                notes = ""

            attendance_records.append(
                {
                    "student_id": student_id,
                    "calendar_date": school_day.strftime("%Y-%m-%d"),
                    "status": status,
                    "notes": notes,
                    "school_year_id": school_year_id,
                }
            )

        return attendance_records

    def generate_all_attendance(
        self, calendar_df: pd.DataFrame, students_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate attendance for all students across all school years."""
        logger.info(
            "Starting attendance generation for all students across all years..."
        )

        all_attendance = []
        attendance_id = 1

        # Get unique school years
        school_years = sorted(students_df["school_year_id"].unique())

        for school_year_id in school_years:
            logger.info(f"Processing school year {school_year_id}...")

            # Get school days for this year
            year_calendar = calendar_df[calendar_df["school_year_id"] == school_year_id]
            school_days = year_calendar[year_calendar["is_school_day"] == True][
                "calendar_date"
            ].tolist()

            if not school_days:
                logger.warning(f"No school days found for year {school_year_id}")
                continue

            # Get students for this year
            year_students = students_df[students_df["school_year_id"] == school_year_id]

            logger.info(
                f"Year {school_year_id}: {len(year_students)} students, {len(school_days)} school days"
            )

            # Generate attendance for each student
            for _, student in year_students.iterrows():
                student_attendance = self.generate_student_yearly_attendance(
                    student["student_id"], school_year_id, school_days
                )

                # Add attendance_id and timestamps
                for record in student_attendance:
                    record["attendance_id"] = attendance_id
                    record["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    record["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    attendance_id += 1

                all_attendance.extend(student_attendance)

            # Log progress
            year_absent = sum(
                1
                for r in all_attendance
                if r["school_year_id"] == school_year_id and r["status"] == "Absent"
            )
            year_tardy = sum(
                1
                for r in all_attendance
                if r["school_year_id"] == school_year_id and r["status"] == "Tardy"
            )
            year_total = sum(
                1 for r in all_attendance if r["school_year_id"] == school_year_id
            )

            if year_total > 0:
                absent_rate = (year_absent / year_total) * 100
                tardy_rate = (year_tardy / year_total) * 100
                logger.info(
                    f"Year {school_year_id} completed: {absent_rate:.1f}% absent, {tardy_rate:.1f}% tardy"
                )

        logger.info(f"Generated {len(all_attendance)} total attendance records")

        # Convert to DataFrame
        attendance_df = pd.DataFrame(all_attendance)

        # Reorder columns to match desired header order
        column_order = [
            "attendance_id",
            "student_id",
            "calendar_date",
            "status",
            "notes",
            "created_at",
            "updated_at",
            "school_year_id",
        ]
        attendance_df = attendance_df[column_order]

        return attendance_df

    def generate_summary_stats(self, attendance_df: pd.DataFrame) -> Dict:
        """Generate summary statistics for the attendance data."""
        total_records = len(attendance_df)
        absent_count = len(attendance_df[attendance_df["status"] == "Absent"])
        tardy_count = len(attendance_df[attendance_df["status"] == "Tardy"])
        present_count = len(attendance_df[attendance_df["status"] == "Present"])

        stats = {
            "total_records": total_records,
            "absent_count": absent_count,
            "tardy_count": tardy_count,
            "present_count": present_count,
            "absent_rate": (
                (absent_count / total_records) * 100 if total_records > 0 else 0
            ),
            "tardy_rate": (
                (tardy_count / total_records) * 100 if total_records > 0 else 0
            ),
            "present_rate": (
                (present_count / total_records) * 100 if total_records > 0 else 0
            ),
        }

        # Yearly breakdown
        yearly_stats = {}
        for year_id in sorted(attendance_df["school_year_id"].unique()):
            year_data = attendance_df[attendance_df["school_year_id"] == year_id]
            year_total = len(year_data)
            year_absent = len(year_data[year_data["status"] == "Absent"])
            year_tardy = len(year_data[year_data["status"] == "Tardy"])

            yearly_stats[year_id] = {
                "total": year_total,
                "absent_rate": (
                    (year_absent / year_total) * 100 if year_total > 0 else 0
                ),
                "tardy_rate": (year_tardy / year_total) * 100 if year_total > 0 else 0,
            }

        stats["yearly_breakdown"] = yearly_stats

        # Reason breakdown
        reason_counts = (
            attendance_df[attendance_df["notes"] != ""]["notes"]
            .value_counts()
            .to_dict()
        )
        stats["absence_reasons"] = reason_counts

        return stats


def main():
    """Main function to generate attendance data."""
    import os

    # Set up proper file paths following Luminosity project structure
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    clean_csv_dir = os.path.join(project_root, "data", "clean_csv")

    parser = argparse.ArgumentParser(
        description="Generate decade attendance data for Luminosity School"
    )
    parser.add_argument(
        "--calendar-file",
        default=os.path.join(clean_csv_dir, "school_calendar.csv"),
        help="School calendar CSV file",
    )
    parser.add_argument(
        "--students-file",
        default=os.path.join(clean_csv_dir, "students.csv"),
        help="Students CSV file",
    )
    parser.add_argument(
        "--output-file",
        default=os.path.join(clean_csv_dir, "attendance.csv"),
        help="Output attendance CSV file",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Verify input files exist
    if not os.path.exists(args.calendar_file):
        logger.error(f"Calendar file not found: {args.calendar_file}")
        return

    if not os.path.exists(args.students_file):
        logger.error(f"Students file not found: {args.students_file}")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    # Initialize generator
    generator = AttendanceGenerator(seed=args.seed)

    try:
        logger.info(f"Loading data from:")
        logger.info(f"  Calendar: {args.calendar_file}")
        logger.info(f"  Students: {args.students_file}")

        # Load data
        calendar_df, students_df = generator.load_data(
            args.calendar_file, args.students_file
        )

        # Generate attendance
        attendance_df = generator.generate_all_attendance(calendar_df, students_df)

        # Save to CSV
        attendance_df.to_csv(args.output_file, index=False)
        logger.info(f"Attendance data saved to {args.output_file}")

        # Generate and display summary statistics
        stats = generator.generate_summary_stats(attendance_df)

        print("\n" + "=" * 60)
        print("LUMINOSITY ATTENDANCE GENERATION SUMMARY")
        print("=" * 60)
        print(f"Total Records: {stats['total_records']:,}")
        print(f"Present: {stats['present_count']:,} ({stats['present_rate']:.1f}%)")
        print(f"Absent: {stats['absent_count']:,} ({stats['absent_rate']:.1f}%)")
        print(f"Tardy: {stats['tardy_count']:,} ({stats['tardy_rate']:.1f}%)")

        print(f"\nYearly Breakdown:")
        for year_id, year_stats in stats["yearly_breakdown"].items():
            print(
                f"  Year {year_id}: {year_stats['total']:,} records, "
                f"{year_stats['absent_rate']:.1f}% absent, {year_stats['tardy_rate']:.1f}% tardy"
            )

        print(f"\nTop Absence Reasons:")
        for reason, count in list(stats["absence_reasons"].items())[:5]:
            print(f"  {reason}: {count:,}")

        print(f"\nOutput saved to: {args.output_file}")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Error generating attendance: {str(e)}")
        raise


if __name__ == "__main__":
    main()
