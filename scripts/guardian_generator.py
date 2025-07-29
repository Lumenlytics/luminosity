#!/usr/bin/env python3
"""
Guardian and Student-Guardian Generator for Luminosity School Management System

This script generates realistic guardian data and student-guardian relationships
following the business rules:
- 65% of students share last name with guardians (family households)
  - 60% of those have two parents (Mother + Father)
  - 35% have single mother
  - 5% have single father
- 35% have non-parent guardians (grandparents, aunts, uncles, etc.)
- ~10 students will share names but not parents (different families)

Usage:
    python guardian_generator.py --input students.csv --output-dir ./output
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
import argparse
import os
from typing import Dict, List, Tuple
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GuardianGenerator:
    def __init__(self, seed: int = 42):
        """Initialize the guardian generator with specified random seed."""
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)
        
        # Guardian type mappings based on your schema
        self.guardian_types = {
            1: "Mother",
            2: "Father", 
            3: "Step-Mother",
            4: "Step-Father",
            5: "Legal Guardian",
            6: "Other"
        }
        
        # Non-parent guardian types for the 35% non-family cases
        self.non_parent_types = [3, 4, 5, 6]  # Step-parents, Legal Guardian, Other
        
        # Family structure percentages - adjusted to hit targets more precisely
        self.shared_lastname_rate = 0.63  # 63% share last name (reduced from 65% to hit closer to 65% target)
        self.two_parent_rate = 0.60       # 60% of shared-name families have 2 parents
        self.single_mom_rate = 0.35       # 35% single mom
        self.single_dad_rate = 0.05       # 5% single dad
        
        # Track generated guardians to avoid duplicates
        self.generated_guardians = {}
        self.guardian_counter = 1
        
    def load_students(self, file_path: str) -> pd.DataFrame:
        """Load students from CSV file."""
        logger.info(f"Loading students from {file_path}")
        students_df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(students_df)} students")
        return students_df
    
    def group_students_by_family(self, students_df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Group students by last name to identify potential families."""
        families = defaultdict(list)
        
        for _, student in students_df.iterrows():
            family_key = student['last_name'].lower()
            families[family_key].append(student.to_dict())
        
        logger.info(f"Identified {len(families)} potential family groups")
        return families
    
    def select_different_family_students(self, families: Dict[str, List[Dict]]) -> List[int]:
        """Select ~12-15 students who share names but will have different families."""
        different_family_students = []
        
        # Find families with multiple students
        multi_student_families = [(name, students) for name, students in families.items() 
                                if len(students) > 1]
        
        # Increase the number of "different families" to help reduce shared last name percentage
        target_different = min(15, len(multi_student_families) * 3)  # Increased multiplier
        
        for family_name, students in random.sample(multi_student_families, 
                                                 min(8, len(multi_student_families))):  # More families
            if len(different_family_students) >= target_different:
                break
            # Take 2-3 students from this family to be "different"
            num_different = min(3, len(students), target_different - len(different_family_students))
            selected = random.sample(students, num_different)
            different_family_students.extend([s['student_id'] for s in selected])
        
        logger.info(f"Selected {len(different_family_students)} students for different families")
        return different_family_students
    
    def generate_realistic_email(self, first_name: str, last_name: str) -> str:
        """Generate realistic email address based on name."""
        # Common email patterns
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}{last_name[0].lower()}",
            f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}",
            f"{first_name.lower()}{random.randint(1, 999)}"
        ]
        
        # Common email providers with realistic weights
        providers = [
            ("gmail.com", 0.35),
            ("yahoo.com", 0.20),
            ("hotmail.com", 0.15),
            ("outlook.com", 0.10),
            ("icloud.com", 0.08),
            ("aol.com", 0.05),
            ("comcast.net", 0.03),
            ("verizon.net", 0.02),
            ("att.net", 0.02)
        ]
        
        # Select pattern and provider
        username = random.choice(patterns)
        provider = random.choices([p[0] for p in providers], 
                                weights=[p[1] for p in providers])[0]
        
        return f"{username}@{provider}"
    
    def generate_realistic_phone(self) -> str:
        """Generate realistic US phone number."""
        # US phone number format: (XXX) XXX-XXXX
        # Avoid certain area codes and exchange codes that are invalid
        
        # Valid area codes (avoiding 555, 000, etc.)
        valid_area_codes = [
            201, 202, 203, 205, 206, 207, 208, 209, 210, 212, 213, 214, 215, 216, 217, 218, 219,
            224, 225, 228, 229, 231, 234, 239, 240, 248, 251, 252, 253, 254, 256, 260, 262, 267,
            269, 270, 276, 281, 301, 302, 303, 304, 305, 307, 308, 309, 310, 312, 313, 314, 315,
            316, 317, 318, 319, 320, 321, 323, 325, 330, 331, 334, 336, 337, 339, 347, 351, 352,
            360, 361, 386, 401, 402, 404, 405, 406, 407, 408, 409, 410, 412, 413, 414, 415, 417,
            419, 423, 424, 425, 430, 432, 434, 435, 440, 443, 445, 464, 469, 470, 475, 478, 479,
            480, 484, 501, 502, 503, 504, 505, 507, 508, 509, 510, 512, 513, 515, 516, 517, 518,
            520, 530, 540, 541, 551, 559, 561, 562, 563, 564, 567, 570, 571, 573, 574, 575, 580,
            585, 586, 601, 602, 603, 605, 606, 607, 608, 609, 610, 612, 614, 615, 616, 617, 618,
            619, 620, 623, 626, 628, 629, 630, 631, 636, 641, 646, 650, 651, 660, 661, 662, 667,
            669, 678, 681, 682, 701, 702, 703, 704, 706, 707, 708, 712, 713, 714, 715, 716, 717,
            718, 719, 720, 724, 725, 727, 731, 732, 734, 737, 740, 743, 747, 754, 757, 760, 762,
            763, 765, 770, 772, 773, 774, 775, 779, 781, 785, 786, 787, 801, 802, 803, 804, 805,
            806, 808, 810, 812, 813, 814, 815, 816, 817, 818, 828, 830, 831, 832, 843, 845, 847,
            848, 850, 856, 857, 858, 859, 860, 862, 863, 864, 865, 870, 872, 878, 901, 903, 904,
            906, 907, 908, 909, 910, 912, 913, 914, 915, 916, 917, 918, 919, 920, 925, 928, 929,
            930, 931, 934, 936, 937, 940, 941, 947, 949, 951, 952, 954, 956, 959, 970, 971, 972,
            973, 978, 979, 980, 984, 985, 989
        ]
        
        area_code = random.choice(valid_area_codes)
        
        # Exchange code (second 3 digits) - avoid 555 and other invalid codes
        exchange = random.randint(200, 999)
        while exchange in [555, 800, 888, 877, 866, 855, 844, 833, 822]:
            exchange = random.randint(200, 999)
        
        # Last 4 digits
        last_four = random.randint(0, 9999)
        
        return f"({area_code:03d}) {exchange:03d}-{last_four:04d}"

    def generate_guardian(self, first_name: str, last_name: str, guardian_type_id: int) -> Dict:
        """Generate a single guardian record."""
        # Create unique key to avoid duplicates
        guardian_key = f"{first_name}_{last_name}_{guardian_type_id}"
        
        if guardian_key in self.generated_guardians:
            return self.generated_guardians[guardian_key]
        
        guardian = {
            'guardian_id': self.guardian_counter,
            'first_name': first_name,
            'last_name': last_name,
            'email': self.generate_realistic_email(first_name, last_name),
            'phone': self.generate_realistic_phone()
        }
        
        self.generated_guardians[guardian_key] = guardian
        self.guardian_counter += 1
        
        return guardian
    
    def generate_family_guardians(self, family_students: List[Dict], 
                                different_family_ids: List[int]) -> Tuple[List[Dict], List[Dict]]:
        """Generate guardians for a family group of students."""
        guardians = []
        student_guardians = []
        
        # Group students by whether they're "different family" or not
        same_family_students = [s for s in family_students if s['student_id'] not in different_family_ids]
        diff_family_students = [s for s in family_students if s['student_id'] in different_family_ids]
        
        # Process same-family students together
        if same_family_students:
            family_guardians, family_relationships = self._generate_single_family(same_family_students)
            guardians.extend(family_guardians)
            student_guardians.extend(family_relationships)
        
        # Process different-family students individually
        for student in diff_family_students:
            individual_guardians, individual_relationships = self._generate_single_family([student])
            guardians.extend(individual_guardians)
            student_guardians.extend(individual_relationships)
        
        return guardians, student_guardians
    
    def _generate_single_family(self, students: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Generate guardians for a single family unit."""
        guardians = []
        student_guardians = []
        
        if not students:
            return guardians, student_guardians
        
        family_last_name = students[0]['last_name']
        
        # Determine if this family shares last name with guardians (65% chance)
        shares_last_name = random.random() < self.shared_lastname_rate
        
        if shares_last_name:
            # Family shares last name - determine family structure
            family_guardians, relationships = self._generate_shared_name_family(students, family_last_name)
        else:
            # Non-parent guardians (35% case)
            family_guardians, relationships = self._generate_non_parent_family(students)
        
        guardians.extend(family_guardians)
        student_guardians.extend(relationships)
        
        return guardians, relationships
    
    def _generate_shared_name_family(self, students: List[Dict], 
                                   family_last_name: str) -> Tuple[List[Dict], List[Dict]]:
        """Generate guardians for families that share last names."""
        guardians = []
        student_guardians = []
        
        # Determine family structure
        rand = random.random()
        
        if rand < self.two_parent_rate:
            # Two-parent family (60%)
            mother = self.generate_guardian(
                self.fake.first_name_female(), 
                family_last_name, 
                1  # Mother
            )
            father = self.generate_guardian(
                self.fake.first_name_male(), 
                family_last_name, 
                2  # Father
            )
            
            guardians = [mother, father]
            
            # Link all students in family to both parents
            for student in students:
                student_guardians.extend([
                    {
                        'student_id': student['student_id'],
                        'guardian_id': mother['guardian_id'],
                        'guardian_type_id': 1
                    },
                    {
                        'student_id': student['student_id'],
                        'guardian_id': father['guardian_id'],
                        'guardian_type_id': 2
                    }
                ])
                
        elif rand < self.two_parent_rate + self.single_mom_rate:
            # Single mother (35%)
            mother = self.generate_guardian(
                self.fake.first_name_female(),
                family_last_name,
                1  # Mother
            )
            
            guardians = [mother]
            
            # Link all students to mother
            for student in students:
                student_guardians.append({
                    'student_id': student['student_id'],
                    'guardian_id': mother['guardian_id'],
                    'guardian_type_id': 1
                })
                
        else:
            # Single father (5%)
            father = self.generate_guardian(
                self.fake.first_name_male(),
                family_last_name,
                2  # Father
            )
            
            guardians = [father]
            
            # Link all students to father
            for student in students:
                student_guardians.append({
                    'student_id': student['student_id'],
                    'guardian_id': father['guardian_id'],
                    'guardian_type_id': 2
                })
        
        return guardians, student_guardians
    
    def _generate_non_parent_family(self, students: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Generate non-parent guardians (35% case)."""
        guardians = []
        student_guardians = []
        
        # Generate different last name for guardian
        guardian_last_name = self.fake.last_name()
        
        # Weighted selection favoring more realistic non-parent relationships
        # Increase step-parent likelihood to better balance the ratios
        guardian_type_weights = {
            3: 0.35,  # Step-Mother (increased weight)
            4: 0.35,  # Step-Father (increased weight) 
            5: 0.20,  # Legal Guardian
            6: 0.10   # Other
        }
        
        guardian_type_id = random.choices(
            list(guardian_type_weights.keys()),
            weights=list(guardian_type_weights.values())
        )[0]
        
        # Generate appropriate first name based on type
        if guardian_type_id == 3:  # Step-Mother
            first_name = self.fake.first_name_female()
        elif guardian_type_id == 4:  # Step-Father
            first_name = self.fake.first_name_male()
        else:  # Legal Guardian or Other
            first_name = self.fake.first_name()
        
        guardian = self.generate_guardian(first_name, guardian_last_name, guardian_type_id)
        guardians = [guardian]
        
        # Link all students in this group to the guardian
        for student in students:
            student_guardians.append({
                'student_id': student['student_id'],
                'guardian_id': guardian['guardian_id'],
                'guardian_type_id': guardian_type_id
            })
        
        return guardians, student_guardians
    
    def generate_all_guardians(self, students_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate all guardian and student-guardian data."""
        logger.info("Starting guardian generation process")
        
        # Group students by family name
        families = self.group_students_by_family(students_df)
        
        # Select students for different families
        different_family_students = self.select_different_family_students(families)
        
        all_guardians = []
        all_student_guardians = []
        
        # Process each family group
        for family_name, family_students in families.items():
            family_guardians, family_relationships = self.generate_family_guardians(
                family_students, different_family_students
            )
            
            all_guardians.extend(family_guardians)
            all_student_guardians.extend(family_relationships)
        
        # Convert to DataFrames
        guardians_df = pd.DataFrame(all_guardians)
        student_guardians_df = pd.DataFrame(all_student_guardians)
        
        # Remove duplicates (in case any slipped through)
        guardians_df = guardians_df.drop_duplicates(subset=['guardian_id'])
        
        logger.info(f"Generated {len(guardians_df)} unique guardians")
        logger.info(f"Generated {len(student_guardians_df)} student-guardian relationships")
        
        return guardians_df, student_guardians_df
    
    def save_data(self, guardians_df: pd.DataFrame, student_guardians_df: pd.DataFrame, 
                  output_dir: str):
        """Save generated data to CSV files."""
        os.makedirs(output_dir, exist_ok=True)
        
        guardians_file = os.path.join(output_dir, 'guardians.csv')
        student_guardians_file = os.path.join(output_dir, 'student_guardians.csv')
        
        guardians_df.to_csv(guardians_file, index=False)
        student_guardians_df.to_csv(student_guardians_file, index=False)
        
        logger.info(f"Saved guardians data to {guardians_file}")
        logger.info(f"Saved student-guardians data to {student_guardians_file}")
    
    def generate_summary_report(self, students_df: pd.DataFrame, 
                              student_guardians_df: pd.DataFrame) -> Dict:
        """Generate summary statistics for validation."""
        total_students = len(students_df)
        
        # Count students by guardian type
        guardian_type_counts = student_guardians_df['guardian_type_id'].value_counts()
        
        # Count students with shared vs different last names
        student_guardian_merged = student_guardians_df.merge(
            students_df[['student_id', 'last_name']], on='student_id'
        )
        
        # This is a simplified check - in reality we'd need to check guardian last names too
        shared_name_approx = len(student_guardian_merged[
            student_guardian_merged['guardian_type_id'].isin([1, 2])
        ]) / total_students
        
        summary = {
            'total_students': total_students,
            'total_guardians': len(student_guardians_df['guardian_id'].unique()),
            'guardian_type_distribution': guardian_type_counts.to_dict(),
            'approximate_shared_name_rate': shared_name_approx,
            'students_with_multiple_guardians': len(
                student_guardians_df.groupby('student_id').filter(lambda x: len(x) > 1)['student_id'].unique()
            )
        }
        
        return summary


def main():
    """Main function to run the guardian generator."""
    parser = argparse.ArgumentParser(description='Generate guardian data for Luminosity School')
    parser.add_argument('--input', default='../data/clean_csv/students.csv', help='Input students CSV file')
    parser.add_argument('--output-dir', default='../data/clean_csv', help='Output directory for CSV files')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = GuardianGenerator(seed=args.seed)
    
    # Load students data
    students_df = generator.load_students(args.input)
    
    # Generate guardian data
    guardians_df, student_guardians_df = generator.generate_all_guardians(students_df)
    
    # Save data
    generator.save_data(guardians_df, student_guardians_df, args.output_dir)
    
    # Generate and print summary report
    summary = generator.generate_summary_report(students_df, student_guardians_df)
    
    print("\n" + "="*50)
    print("GUARDIAN GENERATION SUMMARY")
    print("="*50)
    print(f"Total Students: {summary['total_students']}")
    print(f"Total Guardians: {summary['total_guardians']}")
    print(f"Approximate Shared Name Rate: {summary['approximate_shared_name_rate']:.2%}")
    print(f"Students with Multiple Guardians: {summary['students_with_multiple_guardians']}")
    print("\nGuardian Type Distribution:")
    for type_id, count in summary['guardian_type_distribution'].items():
        type_name = generator.guardian_types.get(type_id, f"Type {type_id}")
        percentage = (count / summary['total_students']) * 100
        print(f"  {type_name}: {count} ({percentage:.1f}%)")
    
    print(f"\nFiles saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
    