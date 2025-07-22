#!/usr/bin/env python3
# flake8: noqa
"""
Analyze Upload Failures

Read the log file and identify specific error patterns.

Usage (run from scripts/ folder):
    cd scripts
    python analyze_upload_failures.py
"""

import os
import re
from collections import defaultdict
from pathlib import Path


def find_latest_log():
    """Find the most recent upload log file."""
    script_dir = Path(__file__).parent
    log_files = list(script_dir.glob("luminosity_upload_*.log"))

    if not log_files:
        print("❌ No log files found!")
        return None

    # Get the most recent log file
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    print(f"📄 Analyzing log file: {latest_log.name}")
    return latest_log


def analyze_log_file(log_file):
    """Analyze the log file for error patterns."""

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read log file: {e}")
        return

    print("\n🔍 ANALYZING UPLOAD FAILURES")
    print("=" * 50)

    # Find all error messages
    error_patterns = {
        "batch_failures": re.findall(
            r"❌ Upload failed for (\w+) batch \d+: (.+)", content
        ),
        "table_failures": re.findall(
            r"❌ Upload failed for (\w+) \(\d+\.\d+% success rate\)", content
        ),
        "processing_failures": re.findall(r"❌ Failed to process (\w+): (.+)", content),
    }

    # Analyze batch failures (most detailed)
    if error_patterns["batch_failures"]:
        print("🚨 BATCH-LEVEL FAILURES:")
        error_counts = defaultdict(list)

        for table, error in error_patterns["batch_failures"]:
            error_counts[table].append(error)

        for table, errors in error_counts.items():
            print(f"\n   📋 {table}:")
            unique_errors = list(set(errors))
            for error in unique_errors[:3]:  # Show first 3 unique errors
                count = errors.count(error)
                print(f"      ❌ {error} (x{count})")

    # Check for specific error types
    common_issues = {
        "foreign_key": ["foreign key", "violates", "constraint", "fkey"],
        "data_type": ["invalid input", "type", "format", "conversion"],
        "permission": ["permission", "access", "denied", "role"],
        "timeout": ["timeout", "connection", "network"],
        "unique_constraint": ["unique", "duplicate", "already exists"],
        "null_constraint": ["null", "not-null", "required"],
    }

    print(f"\n📊 ERROR PATTERN ANALYSIS:")
    total_errors = len(error_patterns["batch_failures"])

    for issue_type, keywords in common_issues.items():
        count = 0
        for table, error in error_patterns["batch_failures"]:
            if any(keyword in error.lower() for keyword in keywords):
                count += 1

        if count > 0:
            percentage = (count / total_errors) * 100
            print(f"   {issue_type:20}: {count:3} errors ({percentage:4.1f}%)")

    # Find the most problematic tables
    print(f"\n🎯 MOST PROBLEMATIC TABLES:")
    table_error_counts = defaultdict(int)
    for table, error in error_patterns["batch_failures"]:
        table_error_counts[table] += 1

    # Sort by error count
    sorted_tables = sorted(table_error_counts.items(), key=lambda x: x[1], reverse=True)
    for table, count in sorted_tables[:5]:
        print(f"   {table:20}: {count:3} failed batches")

    # Look for specific table patterns
    print(f"\n📋 TABLE-SPECIFIC ISSUES:")

    failed_tables = [
        "school_years",
        "terms",
        "students",
        "school_calendar",
        "assignments",
        "grades",
        "attendance",
        "discipline_reports",
        "standardized_tests",
        "payments",
    ]

    successful_tables = [
        "departments",
        "grade_levels",
        "guardian_types",
        "fee_types",
        "periods",
        "classrooms",
        "subjects",
        "teachers",
        "guardians",
        "teacher_subjects",
        "classes",
        "enrollments",
        "student_grade_history",
    ]

    print(f"   ✅ Successful: Small reference tables and lookup tables")
    print(f"   ❌ Failed: Large transactional tables with foreign keys")

    # Check for foreign key dependency issues
    dependency_issues = {
        "students": "May depend on grade_levels (✅ working)",
        "school_calendar": "May depend on school_years (❌ failing)",
        "terms": "May depend on school_years (❌ failing)",
        "assignments": "May depend on classes (✅ working) and terms (❌ failing)",
        "grades": "May depend on students (❌ failing) and assignments (❌ failing)",
        "attendance": "May depend on students (❌ failing)",
        "payments": "May depend on guardians (✅ working)",
    }

    print(f"\n🔗 POTENTIAL DEPENDENCY ISSUES:")
    for table, issue in dependency_issues.items():
        if table in failed_tables:
            print(f"   ❌ {table:20}: {issue}")


def suggest_solutions():
    """Suggest solutions based on the analysis."""
    print(f"\n💡 SUGGESTED SOLUTIONS:")
    print("=" * 50)

    print("1. 🎯 FIX FOREIGN KEY ISSUES:")
    print("   - school_years table is failing but other tables depend on it")
    print("   - Upload school_years first separately")
    print("   - Then upload terms (depends on school_years)")
    print("   - Then upload tables that depend on terms")

    print("\n2. 🗂️ TRY SMALLER BATCH SIZES:")
    print("   - Large tables may be timing out")
    print("   - Try: python upload_to_supabase.py --batch-size 100")

    print("\n3. 📋 CHECK DATA INTEGRITY:")
    print("   - Large tables may have data format issues")
    print("   - Check date formats, null values, foreign key references")

    print("\n4. 🔄 SEQUENTIAL UPLOAD:")
    print("   - Upload tables in strict dependency order")
    print("   - school_years → terms → students → assignments → grades")


def main():
    """Main analysis function."""
    log_file = find_latest_log()
    if log_file:
        analyze_log_file(log_file)
        suggest_solutions()

        print(f"\n🎯 NEXT STEPS:")
        print(
            "1. Try smaller batch size: python upload_to_supabase.py --batch-size 100"
        )
        print("2. Check the specific error messages above")
        print("3. Consider uploading problem tables individually")


if __name__ == "__main__":
    main()
