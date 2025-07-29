import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Define the data directory
data_dir = Path(r"C:\Users\Marshall Sisler\Projects\Luminosity\data\consolidated_data")

# Define the files to analyze
files_to_analyze = [
    'students.csv',
    'teachers.csv', 
    'guardians.csv',
    'student_guardians.csv',
    'grades.csv',
    'attendance.csv',
    'assignments.csv',
    'enrollments.csv',
    'classes.csv',
    'school_calendar.csv'
]

# Dictionary to store dataframes
dfs = {}

print("=" * 80)
print("DATA QUALITY ANALYSIS REPORT")
print("=" * 80)
print()

# Load all files and perform basic analysis
for file in files_to_analyze:
    filepath = data_dir / file
    if filepath.exists():
        print(f"\n{'='*60}")
        print(f"ANALYZING: {file}")
        print(f"{'='*60}")
        
        # Load the dataframe
        df = pd.read_csv(filepath)
        dfs[file.replace('.csv', '')] = df
        
        # Basic statistics
        print(f"\nBasic Statistics:")
        print(f"  - Total rows: {len(df):,}")
        print(f"  - Total columns: {len(df.columns)}")
        print(f"  - Columns: {', '.join(df.columns)}")
        
        # Missing values
        missing = df.isnull().sum()
        missing_pct = (missing / len(df)) * 100
        if missing.any():
            print(f"\nMissing Values:")
            for col, count in missing[missing > 0].items():
                print(f"  - {col}: {count:,} ({missing_pct[col]:.2f}%)")
        else:
            print(f"\nMissing Values: None")
        
        # Duplicates check
        id_col = None
        if 'id' in df.columns:
            id_col = 'id'
        elif file.startswith('students'):
            id_col = 'student_id'
        elif file.startswith('teachers'):
            id_col = 'teacher_id'
        elif file.startswith('guardians'):
            id_col = 'guardian_id'
        elif file.startswith('grades'):
            id_col = 'grade_id'
        elif file.startswith('assignments'):
            id_col = 'assignment_id'
        elif file.startswith('classes'):
            id_col = 'class_id'
        
        if id_col and id_col in df.columns:
            dup_count = df[id_col].duplicated().sum()
            print(f"\nDuplicate {id_col}s: {dup_count}")
        
        # Data types
        print(f"\nData Types:")
        for col, dtype in df.dtypes.items():
            print(f"  - {col}: {dtype}")
    else:
        print(f"\nWARNING: {file} not found!")

print("\n" + "="*80)
print("BUSINESS RULE VALIDATION")
print("="*80)

# 1. Grade Distribution Analysis
if 'grades' in dfs:
    print("\n1. GRADE DISTRIBUTION ANALYSIS")
    print("-" * 50)
    grades_df = dfs['grades']
    
    # Calculate grade statistics
    grade_stats = grades_df['score'].describe()
    print(f"\nGrade Statistics:")
    print(f"  - Mean: {grade_stats['mean']:.2f}%")
    print(f"  - Median: {grade_stats['50%']:.2f}%")
    print(f"  - Std Dev: {grade_stats['std']:.2f}")
    
    # Grade distribution buckets
    perfect_grades = (grades_df['score'] >= 95).sum()
    failing_grades = (grades_df['score'] < 70).sum()
    total_grades = len(grades_df)
    
    perfect_pct = (perfect_grades / total_grades) * 100
    failing_pct = (failing_grades / total_grades) * 100
    
    print(f"\nGrade Distribution:")
    print(f"  - Perfect (95-100%): {perfect_grades:,} ({perfect_pct:.2f}%)")
    print(f"  - Failing (<70%): {failing_grades:,} ({failing_pct:.2f}%)")
    print(f"  - Expected perfect: ~3%")
    print(f"  - Expected failing: 3-5%")
    
    # Grade range distribution
    print(f"\nGrade Range Distribution:")
    ranges = [
        (0, 60, "F (0-59%)"),
        (60, 70, "D (60-69%)"),
        (70, 80, "C (70-79%)"),
        (80, 90, "B (80-89%)"),
        (90, 95, "A (90-94%)"),
        (95, 101, "A+ (95-100%)")
    ]
    
    for low, high, label in ranges:
        count = ((grades_df['score'] >= low) & (grades_df['score'] < high)).sum()
        pct = (count / total_grades) * 100
        print(f"  - {label}: {count:,} ({pct:.2f}%)")

# 2. Guardian Relationship Analysis
if 'students' in dfs and 'guardians' in dfs and 'student_guardians' in dfs:
    print("\n2. GUARDIAN RELATIONSHIP ANALYSIS")
    print("-" * 50)
    
    students_df = dfs['students']
    guardians_df = dfs['guardians']
    student_guardians_df = dfs['student_guardians']
    
    # Load guardian types if available
    guardian_types_file = data_dir / 'guardian_types.csv'
    if guardian_types_file.exists():
        guardian_types_df = pd.read_csv(guardian_types_file)
        guardian_type_map = dict(zip(guardian_types_df['guardian_type_id'], guardian_types_df['label']))
    else:
        guardian_type_map = {}
    
    # Add relationship labels to student_guardians
    student_guardians_df['relationship'] = student_guardians_df['guardian_type_id'].map(guardian_type_map)
    
    # Merge to analyze relationships
    student_guardian_full = student_guardians_df.merge(
        students_df[['student_id', 'last_name']], 
        left_on='student_id', 
        right_on='student_id', 
        suffixes=('', '_student')
    ).merge(
        guardians_df[['guardian_id', 'last_name']], 
        left_on='guardian_id', 
        right_on='guardian_id',
        suffixes=('_student', '_guardian')
    )
    
    # Calculate shared last names
    shared_names = (student_guardian_full['last_name_student'] == student_guardian_full['last_name_guardian']).sum()
    total_relationships = len(student_guardian_full)
    shared_pct = (shared_names / total_relationships) * 100
    
    print(f"\nShared Last Names:")
    print(f"  - Students with guardian's last name: {shared_names:,} ({shared_pct:.2f}%)")
    print(f"  - Expected: ~65%")
    
    # Analyze relationship types
    print(f"\nRelationship Types:")
    relationship_counts = student_guardian_full['relationship'].value_counts()
    for rel, count in relationship_counts.items():
        pct = (count / total_relationships) * 100
        print(f"  - {rel}: {count:,} ({pct:.2f}%)")
    
    # Analyze family structures (two-parent vs single parent)
    family_structures = student_guardian_full.groupby('student_id')['relationship'].apply(list).reset_index()
    
    two_parent = 0
    single_mother = 0
    single_father = 0
    other = 0
    
    for _, row in family_structures.iterrows():
        relationships = row['relationship']
        if 'Mother' in relationships and 'Father' in relationships:
            two_parent += 1
        elif 'Mother' in relationships and 'Father' not in relationships:
            single_mother += 1
        elif 'Father' in relationships and 'Mother' not in relationships:
            single_father += 1
        else:
            other += 1
    
    total_families = len(family_structures)
    print(f"\nFamily Structures:")
    print(f"  - Two-parent families: {two_parent:,} ({(two_parent/total_families)*100:.2f}%)")
    print(f"  - Single mother families: {single_mother:,} ({(single_mother/total_families)*100:.2f}%)")
    print(f"  - Single father families: {single_father:,} ({(single_father/total_families)*100:.2f}%)")
    print(f"  - Other arrangements: {other:,} ({(other/total_families)*100:.2f}%)")

# 3. Attendance Analysis
if 'attendance' in dfs:
    print("\n3. ATTENDANCE ANALYSIS")
    print("-" * 50)
    
    attendance_df = dfs['attendance']
    
    # Calculate attendance rates per student
    student_attendance = attendance_df.groupby('student_id')['status'].value_counts().unstack(fill_value=0)
    student_attendance['total'] = student_attendance.sum(axis=1)
    
    # Calculate rates
    if 'Absent' in student_attendance.columns:
        student_attendance['absence_rate'] = (student_attendance['Absent'] / student_attendance['total']) * 100
        avg_absence = student_attendance['absence_rate'].mean()
        print(f"\nAbsence Rate:")
        print(f"  - Average absence rate: {avg_absence:.2f}%")
        print(f"  - Expected: ~5%")
    
    if 'Tardy' in student_attendance.columns:
        student_attendance['tardy_rate'] = (student_attendance['Tardy'] / student_attendance['total']) * 100
        avg_tardy = student_attendance['tardy_rate'].mean()
        print(f"\nTardy Rate:")
        print(f"  - Average tardy rate: {avg_tardy:.2f}%")
        print(f"  - Expected: ~3%")
    
    # Status distribution
    print(f"\nOverall Attendance Status Distribution:")
    status_counts = attendance_df['status'].value_counts()
    total_records = len(attendance_df)
    for status, count in status_counts.items():
        pct = (count / total_records) * 100
        print(f"  - {status}: {count:,} ({pct:.2f}%)")

# 4. Assignment Frequency Analysis
if 'assignments' in dfs and 'classes' in dfs:
    print("\n4. ASSIGNMENT FREQUENCY ANALYSIS")
    print("-" * 50)
    
    assignments_df = dfs['assignments']
    
    # Convert date columns to datetime
    if 'assigned_date' in assignments_df.columns:
        assignments_df['assigned_date'] = pd.to_datetime(assignments_df['assigned_date'])
        date_col = 'assigned_date'
    else:
        assignments_df['due_date'] = pd.to_datetime(assignments_df['due_date'])
        date_col = 'due_date'
    
    # Calculate assignments per week per class
    assignments_df['week'] = assignments_df[date_col].dt.isocalendar().week
    assignments_df['year'] = assignments_df[date_col].dt.year
    
    weekly_assignments = assignments_df.groupby(['class_id', 'year', 'week']).size()
    avg_weekly = weekly_assignments.mean()
    
    print(f"\nAssignment Frequency:")
    print(f"  - Average assignments per week per class: {avg_weekly:.2f}")
    print(f"  - Expected: ~2")
    
    # Assignments by type
    if 'assignment_type' in assignments_df.columns:
        print(f"\nAssignment Types:")
        type_counts = assignments_df['assignment_type'].value_counts()
        for atype, count in type_counts.items():
            pct = (count / len(assignments_df)) * 100
            print(f"  - {atype}: {count:,} ({pct:.2f}%)")

# 5. Sibling Analysis
if 'students' in dfs and 'guardians' in dfs and 'student_guardians' in dfs:
    print("\n5. SIBLING ANALYSIS")
    print("-" * 50)
    
    # Find siblings by matching guardian relationships
    # Students who share at least one guardian are likely siblings
    sibling_groups = student_guardians_df.groupby('guardian_id')['student_id'].apply(list).reset_index()
    sibling_groups = sibling_groups[sibling_groups['student_id'].apply(len) > 1]
    
    # Count siblings per student
    sibling_count = {}
    for _, row in sibling_groups.iterrows():
        students = row['student_id']
        num_siblings = len(students) - 1
        for student in students:
            if student not in sibling_count:
                sibling_count[student] = 0
            sibling_count[student] = max(sibling_count[student], num_siblings)
    
    # Add students with no siblings
    all_students = set(students_df['student_id'])
    for student in all_students:
        if student not in sibling_count:
            sibling_count[student] = 0
    
    # Calculate sibling distribution
    sibling_dist = pd.Series(sibling_count).value_counts().sort_index()
    total_students = len(all_students)
    
    print(f"\nSibling Distribution:")
    expected = {0: None, 1: None, 2: 15, 3: 8, 4: 5, 5: 2}
    for num_siblings, count in sibling_dist.items():
        pct = (count / total_students) * 100
        expected_pct = expected.get(num_siblings, None)
        expected_str = f" (Expected: ~{expected_pct}%)" if expected_pct else ""
        print(f"  - {num_siblings} siblings: {count:,} students ({pct:.2f}%){expected_str}")

print("\n" + "="*80)
print("FOREIGN KEY RELATIONSHIP VALIDATION")
print("="*80)

# Check foreign key relationships
fk_checks = [
    ('student_guardians', 'student_id', 'students', 'student_id'),
    ('student_guardians', 'guardian_id', 'guardians', 'guardian_id'),
    ('grades', 'student_id', 'students', 'student_id'),
    ('grades', 'assignment_id', 'assignments', 'assignment_id'),
    ('attendance', 'student_id', 'students', 'student_id'),
    ('enrollments', 'student_id', 'students', 'student_id'),
    ('enrollments', 'class_id', 'classes', 'class_id'),
    ('assignments', 'class_id', 'classes', 'class_id'),
]

print("\nForeign Key Integrity Check:")
for child_table, child_col, parent_table, parent_col in fk_checks:
    if child_table in dfs and parent_table in dfs:
        child_df = dfs[child_table]
        parent_df = dfs[parent_table]
        
        if child_col in child_df.columns and parent_col in parent_df.columns:
            child_values = set(child_df[child_col].dropna())
            parent_values = set(parent_df[parent_col])
            
            orphaned = child_values - parent_values
            if orphaned:
                print(f"\n  FAIL {child_table}.{child_col} -> {parent_table}.{parent_col}")
                print(f"     Found {len(orphaned)} orphaned references")
            else:
                print(f"  OK {child_table}.{child_col} -> {parent_table}.{parent_col}: Valid")

print("\n" + "="*80)
print("DATA INTEGRITY ISSUES SUMMARY")
print("="*80)

# Summarize critical issues
print("\nCRITICAL ISSUES:")
critical_issues = []

# Check grade distribution
if 'grades' in dfs:
    grades_df = dfs['grades']
    avg_grade = grades_df['score'].mean()
    if avg_grade < 85 or avg_grade > 90:
        critical_issues.append(f"Grade average ({avg_grade:.2f}%) outside expected range (85-90%)")
    
    perfect_pct = ((grades_df['score'] >= 95).sum() / len(grades_df)) * 100
    if abs(perfect_pct - 3) > 1:
        critical_issues.append(f"Perfect grade percentage ({perfect_pct:.2f}%) deviates from expected ~3%")

if critical_issues:
    for i, issue in enumerate(critical_issues, 1):
        print(f"  {i}. {issue}")
else:
    print("  No critical issues found")

print("\nIMPORTANT ISSUES:")
important_issues = []

# Check attendance rates
if 'attendance' in dfs and 'absence_rate' in locals():
    if abs(avg_absence - 5) > 1:
        important_issues.append(f"Average absence rate ({avg_absence:.2f}%) deviates from expected ~5%")

# Check shared last names
if 'shared_pct' in locals():
    if abs(shared_pct - 65) > 5:
        important_issues.append(f"Shared last name percentage ({shared_pct:.2f}%) deviates from expected ~65%")

if important_issues:
    for i, issue in enumerate(important_issues, 1):
        print(f"  {i}. {issue}")
else:
    print("  No important issues found")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)

print("\n1. Data Quality Improvements:")
print("   - Review and validate all foreign key relationships")
print("   - Ensure consistent data types across related columns")
print("   - Add data validation rules to prevent future integrity issues")

print("\n2. Business Rule Alignment:")
print("   - Adjust grade generation to achieve 85-90% average")
print("   - Fine-tune perfect/failing grade distributions")
print("   - Review guardian relationship assignments")

print("\n3. Next Steps:")
print("   - Run detailed validation on date ranges in school_calendar.csv")
print("   - Verify term_id consistency across assignments and grades")
print("   - Check for logical inconsistencies in enrollment dates")

print("\n" + "="*80)
print("END OF REPORT")
print("="*80)