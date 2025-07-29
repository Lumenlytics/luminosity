Claude Code Instructions: Fix Luminosity School Calendar Generator
🎯 Objective
Fix all issues in the calendar_generation.py script located in the Projects/Luminosity/scripts/ directory. The script currently has 187 problems that need to be resolved to generate a proper school calendar CSV file.

📁 File Location
Target File: Projects/Luminosity/scripts/calendar_generation.py
Output Directory: Projects/Luminosity/data/clean_csvs/
Output File: school_calendar.csv
🔧 Required Fixes
1. Syntax and Import Issues
Fix any Python syntax errors
Verify all imports are correct and available
Ensure proper indentation throughout
Fix any unclosed brackets, quotes, or parentheses
2. Date and Time Logic Fixes
Ensure all date calculations are accurate
Fix Easter calculation algorithm if broken
Verify federal holiday calculations (Labor Day, MLK Day, Presidents Day, Memorial Day, etc.)
Fix Thanksgiving calculation (fourth Thursday in November)
Ensure proper date range handling (August 1, 2016 to June 30, 2026)
3. School Year Logic Validation
Verify school year definitions and date ranges
Ensure each school year has approximately 180 instructional days
Fix any overlap or gap issues between school years
Validate start dates (late August) and end dates (early June)
4. Break Period Logic
Fix fall break definitions (1-2 days in October)
Correct Thanksgiving break (3-5 days including Thursday-Monday)
Validate winter break (December 22 - January 2, spanning two calendar years)
Fix spring break (1 week in March/April for each year)
5. Weather and Emergency Day Generation
Fix weather day generation to ensure 2-5 days per year for Maine
Ensure weather days only occur on weekdays during school year
Prevent weather days from conflicting with holidays or breaks
Fix COVID-19 closure logic for 2020-2022 period
6. Teacher and Professional Development Days
Ensure teacher work days (5-10 per year) are properly scheduled
Fix professional development days (3-5 per year)
Prevent these days from occurring on weekends or holidays
7. Testing Day Logic
Fix PSAT day calculation (October, typically third Wednesday)
Correct SAT school day scheduling (spring for 11th graders)
Fix AP exam weeks (first two weeks of May)
Ensure graduation ceremony date is properly calculated
8. Day Type Precedence and Conflicts
Implement proper precedence order:
Weekends (Saturday/Sunday) - never school days
Federal holidays - override other labels
School breaks - respect holidays within breaks
Weather/emergency days - only on potential school days
Teacher work/PD days - only on potential school days
Testing days - special school days
Special events - still school days with activities
Regular school days - weekdays during school year
Summer break - outside school year
9. Data Validation Logic
Ensure is_school_day is never True for weekends
Ensure is_holiday is properly set for federal holidays
Validate that weather days don't occur on weekends or holidays
Fix any logic that allows conflicting day types
10. CSV Generation and File I/O
Fix directory creation and file path handling
Ensure proper CSV formatting with all required columns:
calendar_date (YYYY-MM-DD format)
school_year_id (integer 1-10 or empty for summer)
is_school_day (boolean)
is_holiday (boolean)
label (descriptive text)
created_at (timestamp)
updated_at (timestamp)
Fix any pandas DataFrame issues
Ensure proper error handling for file operations
11. Random Number Generation
Fix random seed usage for reproducible results
Ensure random selection logic for weather days works correctly
Fix any issues with random date selection
12. Function and Variable Scope Issues
Fix any undefined variable references
Ensure all helper functions are properly defined
Fix any scope issues with nested functions
13. Special Event Logic (Optional)
Fix homecoming and spirit week calculations
Ensure field day scheduling works properly
Validate special events only occur during school year
14. COVID-19 Pandemic Adjustments
Fix 2019-2020 extended closure (starting March 13, 2020)
Correct 2020-2021 hybrid/remote learning day generation
Fix 2021-2022 quarantine day logic
15. Statistics and Validation Output
Fix comprehensive statistics calculation
Ensure proper day type counting and validation
Fix average school days calculation and 180-day requirement validation
Correct file size and summary statistics
🎯 Expected Outcome
After fixes, the script should:

Run without any errors from the Projects/Luminosity/scripts/ directory
Generate exactly 3,652 calendar entries (Aug 1, 2016 to Jun 30, 2026)
Create a valid CSV file at Projects/Luminosity/data/clean_csvs/school_calendar.csv
Have approximately 180 school days per academic year (175-185 acceptable range)
Show no weekends marked as school days
Display comprehensive validation statistics
Have no logical conflicts between day types
🔍 Validation Requirements
The fixed script must validate:

Weekend Protection: No Saturday/Sunday should have is_school_day = True
Holiday Logic: All federal holidays should have is_holiday = True
School Day Count: Each school year should have 175-185 instructional days
Date Range: All dates from 2016-08-01 to 2026-06-30 are included
No Conflicts: No date should have conflicting day type assignments
Weather Days: 2-5 weather-related closure days per year, only on weekdays
Break Periods: All major breaks properly defined and non-overlapping
File Output: Valid CSV with all required columns and proper formatting
🚀 Execution Instructions
Analyze the current script to identify all 187 issues
Fix each issue systematically, starting with syntax errors
Test date calculation functions individually
Validate logic flow and precedence rules
Run the script to generate the calendar
Verify output statistics meet all requirements
Confirm CSV file is properly formatted and complete
📊 Success Metrics
✅ Script runs without errors
✅ Generates 3,652 total calendar entries
✅ Each school year has ~180 instructional days
✅ No weekends marked as school days
✅ All federal holidays properly flagged
✅ Weather days realistic for Maine (2-5 per year)
✅ COVID-19 timeline accurate for 2020-2022
✅ CSV file properly formatted and importable
✅ Comprehensive validation statistics displayed
The fixed script should be production-ready for the Luminosity school management system database.
