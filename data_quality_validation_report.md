# Data Quality Validation Report
## Luminosity School Data Analysis

### Executive Summary

This report presents a comprehensive analysis of the CSV files in the `consolidated_data` folder. The analysis identified several critical data quality issues that require immediate attention, particularly around grade distributions, duplicate IDs, and sibling relationships.

---

## 1. Data Overview

### Files Analyzed
- **students.csv**: 5,382 records
- **teachers.csv**: 620 records  
- **guardians.csv**: 3,213 records
- **student_guardians.csv**: 8,589 records
- **grades.csv**: 2,414,225 records
- **attendance.csv**: 968,760 records
- **assignments.csv**: 57,714 records
- **enrollments.csv**: 34,507 records
- **classes.csv**: 825 records
- **school_calendar.csv**: 2,852 records

### Key Findings Summary
- **Critical Issues**: 3 major problems identified
- **Data Integrity**: Significant duplicate ID issues across multiple tables
- **Business Rules**: Multiple violations of expected distributions

---

## 2. Critical Data Quality Issues

### 2.1 Massive Duplicate ID Problem
- **Students**: 4,411 duplicate IDs out of 5,382 records (82% duplicates!)
- **Teachers**: 522 duplicate IDs out of 620 records (84% duplicates!)
- **Guardians**: 2,777 duplicate IDs out of 3,213 records (86% duplicates!)
- **Grades**: 2,103,974 duplicate IDs out of 2,414,225 records (87% duplicates!)
- **Assignments**: 50,959 duplicate IDs out of 57,714 records (88% duplicates!)
- **Classes**: 728 duplicate IDs out of 825 records (88% duplicates!)

**Impact**: Primary key integrity completely compromised across the database

### 2.2 Grade Distribution Catastrophically Wrong
- **Current Average**: 37.79% (Expected: 85-90%)
- **Perfect Grades (95-100%)**: 0.12% (Expected: ~3%)
- **Failing Grades (<70%)**: 79.60% (Expected: 3-5%)
- **Grade F (0-59%)**: 70.13% of all grades

**Impact**: Grade data appears to be using incorrect scale or has major data corruption

### 2.3 Sibling Relationships Anomaly
- Most students show 0-1 siblings
- Huge spike at 29 siblings (20.08% of students)
- Another spike at 38 siblings (9.68% of students)
- Distribution completely unrealistic with many students having 20+ siblings

**Impact**: Family relationship data appears corrupted or incorrectly joined

---

## 3. Business Rule Violations

### 3.1 Guardian Relationships
- **Shared Last Names**: 37.70% (Expected: ~65%)
- **Family Structures**:
  - Two-parent families: 11.53% (Expected: ~60%)
  - Single mother: 24.92% (Expected: ~35%)
  - Single father: 26.06% (Expected: ~5%)
  - Other: 37.49%

### 3.2 Attendance Patterns
- **Absence Rate**: 2.48% (Expected: ~5%) - Lower than expected
- **Tardy Rate**: 2.78% (Expected: ~3%) - Close to expected
- **Present Rate**: 92.22% - Higher than realistic

### 3.3 Assignment Frequency
- **Average per week per class**: 2.08 (Expected: ~2) ✓
- This is one of the few metrics meeting expectations

---

## 4. Data Type and Structure Issues

### 4.1 Inconsistent ID Types
- Most IDs are `int64` type
- But `attendance_id` and `enrollment_id` are stored as `object` (string)

### 4.2 Missing Values
- **school_calendar.csv**:
  - holiday_name: 97.97% missing (expected for non-holidays)
  - comment: 65.11% missing
  - label: 65.11% missing

### 4.3 Date Formats
- All date fields stored as `object` type rather than datetime
- Needs conversion for proper date-based analysis

---

## 5. Recommendations (Priority Order)

### CRITICAL - Immediate Action Required

1. **Fix Primary Key Integrity**
   - Investigate source of duplicate IDs across all tables
   - Appears to be data from multiple years incorrectly combined
   - Consider using composite keys (id + school_year_id)

2. **Correct Grade Data**
   - Grade scores appear to be on wrong scale (0-100 vs 0-1?)
   - May need to multiply all scores by 100
   - Validate score ranges match expected percentages

3. **Fix Sibling Relationships**
   - Review student_guardians join logic
   - Current algorithm creating false sibling relationships
   - Likely counting all students sharing any guardian as siblings

### IMPORTANT - Address Soon

4. **Guardian Relationship Alignment**
   - Review last name matching logic
   - Verify guardian type assignments
   - Correct family structure distributions

5. **Data Type Standardization**
   - Convert all ID columns to consistent type
   - Convert date strings to datetime objects
   - Add proper constraints and validations

### MINOR - Quality Improvements

6. **Attendance Adjustments**
   - Review if absence rates are realistic
   - Check for missing attendance records
   - Validate weekend/holiday exclusions

7. **Foreign Key Validation**
   - Implement referential integrity checks
   - Add cascading rules for multi-year data
   - Create proper indexes for performance

---

## 6. Next Steps

1. **Immediate Investigation**
   - Review data consolidation process that created duplicate IDs
   - Check if grade scores need scale conversion (multiply by 100)
   - Fix sibling calculation algorithm

2. **Data Cleaning**
   - Create unique composite keys using ID + school_year
   - Transform grade scores to proper 0-100 scale
   - Recalculate family relationships correctly

3. **Validation Framework**
   - Implement automated checks for business rules
   - Add data quality monitoring
   - Create exception reports for anomalies

---

## 7. Conclusion

The data shows signs of a flawed consolidation process where multiple years of data were combined without properly handling ID conflicts. The most critical issues are:

1. **Duplicate IDs** making it impossible to uniquely identify records
2. **Grade scale** appears to be decimal (0-1) instead of percentage (0-100)
3. **Sibling logic** counting all students with shared guardians as siblings

These issues must be resolved before the data can be used for any analysis or uploaded to a production system. The data quality problems are systematic rather than random, suggesting issues in the data generation or consolidation process rather than corruption.