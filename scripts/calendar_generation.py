#!/usr/bin/env python3
"""
LUMINOSITY COMPREHENSIVE SCHOOL CALENDAR GENERATOR

Generates a complete school calendar from August 1, 2016 to June 30, 2026
with all required events, holidays, and special days.

Usage: Run from Projects/Luminosity/scripts/ directory
Output: Saves to Projects/Luminosity/data/clean_csv/school_calendar.csv
"""

import pandas as pd
from datetime import datetime, timedelta, date
import random
import os
import sys


def get_easter_monday(year):
    """Calculate Easter Monday using Gauss's Easter algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    
    easter_sunday = date(year, month, day)
    easter_monday = easter_sunday + timedelta(days=1)
    return easter_monday


def generate_complete_calendar():
    """Generate the complete school calendar and save to CSV file."""
    
    # Verify we're running from the correct directory
    current_dir = os.getcwd()
    if not current_dir.endswith(os.path.join('Luminosity', 'scripts')):
        print("Warning: This script should be run from Projects/Luminosity/scripts/")
        print(f"Current directory: {current_dir}")
    
    # Set up output directory
    output_dir = os.path.join('..', 'data', 'clean_csv')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'school_calendar.csv')
    
    print(f"Generating school calendar...")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print(f"Output file: {os.path.abspath(output_file)}")
    
    # School year definitions
    school_years = {
        1: {"start": date(2016, 8, 29), "end": date(2017, 6, 9)},
        2: {"start": date(2017, 8, 28), "end": date(2018, 6, 8)},
        3: {"start": date(2018, 8, 27), "end": date(2019, 6, 7)},
        4: {"start": date(2019, 8, 26), "end": date(2020, 6, 5)},
        5: {"start": date(2020, 8, 24), "end": date(2021, 6, 4)},
        6: {"start": date(2021, 8, 30), "end": date(2022, 6, 10)},
        7: {"start": date(2022, 8, 29), "end": date(2023, 6, 9)},
        8: {"start": date(2023, 8, 28), "end": date(2024, 6, 7)},
        9: {"start": date(2024, 8, 26), "end": date(2025, 6, 6)},
        10: {"start": date(2025, 8, 25), "end": date(2026, 6, 5)}
    }
    
    # Helper functions for federal holidays
    def get_labor_day(year):
        sept_1 = date(year, 9, 1)
        days_to_monday = (7 - sept_1.weekday()) % 7
        return sept_1 + timedelta(days=days_to_monday)
    
    def get_columbus_day(year):
        oct_1 = date(year, 10, 1)
        days_to_monday = (7 - oct_1.weekday()) % 7
        first_monday = oct_1 + timedelta(days=days_to_monday)
        return first_monday + timedelta(days=7)
    
    def get_mlk_day(year):
        jan_1 = date(year, 1, 1)
        days_to_monday = (7 - jan_1.weekday()) % 7
        first_monday = jan_1 + timedelta(days=days_to_monday)
        return first_monday + timedelta(days=14)
    
    def get_presidents_day(year):
        feb_1 = date(year, 2, 1)
        days_to_monday = (7 - feb_1.weekday()) % 7
        first_monday = feb_1 + timedelta(days=days_to_monday)
        return first_monday + timedelta(days=14)
    
    def get_memorial_day(year):
        may_31 = date(year, 5, 31)
        days_back = (may_31.weekday() + 1) % 7
        return may_31 - timedelta(days=days_back)
    
    def get_thanksgiving_day(year):
        nov_1 = date(year, 11, 1)
        days_to_thursday = (3 - nov_1.weekday()) % 7
        first_thursday = nov_1 + timedelta(days=days_to_thursday)
        return first_thursday + timedelta(days=21)
    
    # Generate comprehensive calendar events for all years
    federal_holidays = {}
    special_events = {}
    
    for year in range(2016, 2027):
        # Core federal holidays
        federal_holidays[date(year, 11, 11)] = "Veterans Day"
        federal_holidays[date(year, 12, 25)] = "Christmas Day"
        federal_holidays[date(year, 1, 1)] = "New Year's Day"
        
        if year >= 2016:
            federal_holidays[get_labor_day(year)] = "Labor Day"
            federal_holidays[get_columbus_day(year)] = "Columbus Day"
            federal_holidays[get_thanksgiving_day(year)] = "Thanksgiving Day"
            
        if year >= 2017:
            federal_holidays[get_mlk_day(year)] = "Martin Luther King Jr. Day"
            federal_holidays[get_presidents_day(year)] = "Presidents Day"
            federal_holidays[get_memorial_day(year)] = "Memorial Day"
            # Easter Monday (some regions observe)
            special_events[get_easter_monday(year)] = "Easter Monday"
    
    # Define comprehensive break periods for each school year
    breaks = {
        1: {  # 2016-2017
            "fall": [date(2016, 10, 10)],  # Columbus Day + 1 day
            "thanksgiving": [date(2016, 11, 24), date(2016, 11, 25), date(2016, 11, 28)],  # Thu-Mon
            "winter": [date(2016, 12, 22) + timedelta(days=i) for i in range(12)],  # Dec 22 - Jan 2
            "spring": [date(2017, 3, 13) + timedelta(days=i) for i in range(5)]     # March 13-17
        },
        2: {  # 2017-2018
            "fall": [date(2017, 10, 9)],  # Day after Columbus Day
            "thanksgiving": [date(2017, 11, 23), date(2017, 11, 24), date(2017, 11, 27)],
            "winter": [date(2017, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2018, 3, 19) + timedelta(days=i) for i in range(5)]
        },
        3: {  # 2018-2019
            "fall": [date(2018, 10, 8)],
            "thanksgiving": [date(2018, 11, 22), date(2018, 11, 23), date(2018, 11, 26)],
            "winter": [date(2018, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2019, 4, 8) + timedelta(days=i) for i in range(5)]
        },
        4: {  # 2019-2020 (COVID year)
            "fall": [date(2019, 10, 14)],
            "thanksgiving": [date(2019, 11, 28), date(2019, 11, 29), date(2019, 12, 2)],
            "winter": [date(2019, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2020, 3, 16) + timedelta(days=i) for i in range(5)],
            "covid_closure": []  # Will be handled separately
        },
        5: {  # 2020-2021 (Hybrid year)
            "fall": [date(2020, 10, 12)],
            "thanksgiving": [date(2020, 11, 26), date(2020, 11, 27), date(2020, 11, 30)],
            "winter": [date(2020, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2021, 3, 22) + timedelta(days=i) for i in range(5)]
        },
        6: {  # 2021-2022
            "fall": [date(2021, 10, 11)],
            "thanksgiving": [date(2021, 11, 25), date(2021, 11, 26), date(2021, 11, 29)],
            "winter": [date(2021, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2022, 4, 4) + timedelta(days=i) for i in range(5)]
        },
        7: {  # 2022-2023
            "fall": [date(2022, 10, 10)],
            "thanksgiving": [date(2022, 11, 24), date(2022, 11, 25), date(2022, 11, 28)],
            "winter": [date(2022, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2023, 3, 13) + timedelta(days=i) for i in range(5)]
        },
        8: {  # 2023-2024
            "fall": [date(2023, 10, 9)],
            "thanksgiving": [date(2023, 11, 23), date(2023, 11, 24), date(2023, 11, 27)],
            "winter": [date(2023, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2024, 3, 18) + timedelta(days=i) for i in range(5)]
        },
        9: {  # 2024-2025
            "fall": [date(2024, 10, 14)],
            "thanksgiving": [date(2024, 11, 28), date(2024, 11, 29), date(2024, 12, 2)],
            "winter": [date(2024, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2025, 3, 17) + timedelta(days=i) for i in range(5)]
        },
        10: {  # 2025-2026
            "fall": [date(2025, 10, 13)],
            "thanksgiving": [date(2025, 11, 27), date(2025, 11, 28), date(2025, 12, 1)],
            "winter": [date(2025, 12, 22) + timedelta(days=i) for i in range(12)],
            "spring": [date(2026, 3, 23) + timedelta(days=i) for i in range(5)]
        }
    }
    
    # Generate weather and emergency days for Maine
    random.seed(42)  # For reproducible results
    weather_emergency_days = {}
    
    for year_id in range(1, 11):
        year = 2016 + year_id - 1
        weather_emergency_days[year_id] = {
            "snow_days": [],
            "ice_days": [],
            "storm_days": [],
            "cold_days": [],
            "covid_days": [],
            "remote_days": [],
            "hybrid_days": []
        }
        
        # Weather-related closures (2-5 per year total for Maine)
        total_weather_days = random.randint(2, 5)
        weather_potential = []
        
        # Find potential weather closure days (Dec-Mar, weekdays, during school)
        for month in [12, 1, 2, 3]:
            cal_year = year if month == 12 else year + 1
            for day in range(1, 32):
                try:
                    test_date = date(cal_year, month, day)
                    if (test_date.weekday() < 5 and 
                        school_years[year_id]["start"] <= test_date <= school_years[year_id]["end"] and
                        test_date not in federal_holidays and
                        not any(test_date in break_dates for break_dates in breaks[year_id].values())):
                        weather_potential.append(test_date)
                except ValueError:
                    continue
        
        # Distribute weather days among types
        if len(weather_potential) >= total_weather_days:
            weather_days = random.sample(weather_potential, total_weather_days)
            # Randomly assign types
            for i, day in enumerate(weather_days):
                day_type = random.choice(["snow", "ice", "storm", "cold"])
                weather_emergency_days[year_id][f"{day_type}_days"].append(day)
        
        # COVID-19 specific adjustments (2020-2022)
        if year_id == 4:  # 2019-2020: COVID closure starts March 13
            covid_start = date(2020, 3, 13)
            covid_end = school_years[year_id]["end"]
            current = covid_start
            while current <= covid_end:
                if current.weekday() < 5:  # Weekdays only
                    weather_emergency_days[year_id]["covid_days"].append(current)
                current += timedelta(days=1)
                
        elif year_id == 5:  # 2020-2021: Hybrid year with remote/hybrid days
            # Some remote learning days
            remote_potential = []
            for month in [9, 10, 11, 1, 2, 3]:
                cal_year = year if month >= 9 else year + 1
                for day in range(1, 32):
                    try:
                        test_date = date(cal_year, month, day)
                        if (test_date.weekday() < 5 and 
                            school_years[year_id]["start"] <= test_date <= school_years[year_id]["end"] and
                            test_date not in federal_holidays and
                            not any(test_date in break_dates for break_dates in breaks[year_id].values())):
                            remote_potential.append(test_date)
                    except ValueError:
                        continue
            
            # 10-15 remote learning days
            num_remote = random.randint(10, 15)
            weather_emergency_days[year_id]["remote_days"] = random.sample(
                remote_potential, min(num_remote, len(remote_potential)))
            
            # 15-20 hybrid learning days
            remaining_days = [d for d in remote_potential if d not in weather_emergency_days[year_id]["remote_days"]]
            num_hybrid = random.randint(15, 20)
            weather_emergency_days[year_id]["hybrid_days"] = random.sample(
                remaining_days, min(num_hybrid, len(remaining_days)))
                
        elif year_id == 6:  # 2021-2022: Some COVID quarantine days
            quarantine_potential = []
            for month in [9, 10, 11, 12, 1]:
                cal_year = year if month >= 9 else year + 1
                for day in range(1, 32):
                    try:
                        test_date = date(cal_year, month, day)
                        if (test_date.weekday() < 5 and 
                            school_years[year_id]["start"] <= test_date <= school_years[year_id]["end"]):
                            quarantine_potential.append(test_date)
                    except ValueError:
                        continue
            
            # 3-7 COVID quarantine days
            num_covid = random.randint(3, 7)
            weather_emergency_days[year_id]["covid_days"] = random.sample(
                quarantine_potential, min(num_covid, len(quarantine_potential)))
    
    # Teacher work days (5-10 per year)
    teacher_work_days = {}
    for year_id, year_info in school_years.items():
        year = 2015 + year_id
        teacher_work_days[year_id] = [
            # Pre-school teacher work days (2 days before school starts)
            year_info["start"] - timedelta(days=2),  
            year_info["start"] - timedelta(days=1),
            # Mid-year teacher work day (day after winter break)
            date(year + 1, 1, 3),  # January 3
            # Spring teacher work day
            date(year + 1, 3, 1),  # March 1
            # End of year teacher work day
            year_info["end"] + timedelta(days=1)
        ]
    
    # Professional development days (3-5 per year)
    professional_dev_days = {}
    for year_id in range(1, 11):
        year = 2016 + year_id - 1
        professional_dev_days[year_id] = [
            date(year, 10, 15),  # October PD day
            date(year + 1, 2, 15),  # February PD day
            date(year + 1, 4, 15)   # April PD day
        ]
    
    # Testing days
    testing_days = {}
    for year_id in range(1, 11):
        year = 2016 + year_id - 1
        
        # PSAT day (third Wednesday in October)
        oct_1 = date(year, 10, 1)
        days_to_wed = (2 - oct_1.weekday()) % 7
        first_wed = oct_1 + timedelta(days=days_to_wed)
        psat_day = first_wed + timedelta(days=14)
        
        # SAT school day (spring, typically March)
        sat_day = date(year + 1, 3, 10)
        
        # AP exam weeks (first two weeks of May)
        ap_weeks = []
        may_1 = date(year + 1, 5, 1)
        for i in range(10):  # First two weeks
            test_date = may_1 + timedelta(days=i)
            if test_date.weekday() < 5:  # Weekdays only
                ap_weeks.append(test_date)
        
        # Graduation (first Friday in June)
        june_1 = date(year + 1, 6, 1)
        days_to_fri = (4 - june_1.weekday()) % 7
        graduation = june_1 + timedelta(days=days_to_fri)
        
        testing_days[year_id] = {
            "psat_day": psat_day,
            "sat_day": sat_day,
            "ap_weeks": ap_weeks,
            "graduation": graduation
        }
    
    # Special events
    special_events_by_year = {}
    for year_id in range(1, 11):
        year = 2016 + year_id - 1
        
        # Homecoming (October Friday)
        homecoming = date(year, 10, 20)
        while homecoming.weekday() != 4:  # Find Friday
            homecoming += timedelta(days=1)
        
        # Spirit week (week before homecoming)
        spirit_week = []
        for i in range(5):
            spirit_week.append(homecoming - timedelta(days=4-i))
        
        # Field day (May)
        field_day = date(year + 1, 5, 20)
        while field_day.weekday() != 4:  # Find Friday
            field_day += timedelta(days=1)
        
        special_events_by_year[year_id] = {
            "homecoming": homecoming,
            "spirit_week": spirit_week,
            "field_day": field_day
        }
    
    # Generate calendar data
    calendar_data = []
    start_date = date(2016, 8, 1)
    end_date = date(2026, 6, 30)
    
    current_date = start_date
    while current_date <= end_date:
        # Determine school year
        school_year_id = None
        for year_id, year_info in school_years.items():
            if year_info["start"] <= current_date <= year_info["end"]:
                school_year_id = year_id
                break
        
        # Determine day type with proper precedence and validation
        is_school_day = False
        is_holiday = False
        label = ""
        
        # 1. FIRST PRIORITY: Check if it's a weekend (never a school day)
        if current_date.weekday() >= 5:  # Saturday=5, Sunday=6
            label = "Saturday" if current_date.weekday() == 5 else "Sunday"
            is_school_day = False
            is_holiday = False
        
        # 2. SECOND PRIORITY: Check if it's a federal holiday (overrides other labels but not weekends)
        elif current_date in federal_holidays:
            is_holiday = True
            is_school_day = False
            label = federal_holidays[current_date]
        
        # 3. THIRD PRIORITY: Check if it's during a school break
        elif school_year_id and any(current_date in break_dates for break_type, break_dates in breaks[school_year_id].items() if break_type != "covid_closure"):
            is_school_day = False
            if current_date in breaks[school_year_id]["thanksgiving"]:
                # Check if it's also a federal holiday (Thanksgiving Day)
                if current_date in federal_holidays:
                    label = federal_holidays[current_date]
                    is_holiday = True
                else:
                    label = "Thanksgiving Break"
            elif current_date in breaks[school_year_id]["winter"]:
                # Check if it's also a federal holiday (Christmas/New Year's)
                if current_date in federal_holidays:
                    label = federal_holidays[current_date]
                    is_holiday = True
                else:
                    label = "Winter Break"
            elif current_date in breaks[school_year_id]["spring"]:
                label = "Spring Break"
            elif current_date in breaks[school_year_id]["fall"]:
                label = "Fall Break"
        
        # 4. FOURTH PRIORITY: Check if it's a weather/emergency day (only on potential school days)
        elif (school_year_id and 
              current_date.weekday() < 5 and  # Must be weekday
              current_date not in federal_holidays):  # Must not be holiday
            
            found_weather_day = False
            for day_type in ["snow_days", "ice_days", "storm_days", "cold_days", "covid_days", "remote_days", "hybrid_days"]:
                if current_date in weather_emergency_days[school_year_id][day_type]:
                    is_school_day = False
                    found_weather_day = True
                    if day_type == "snow_days":
                        label = "Snow Day"
                    elif day_type == "ice_days":
                        label = "Ice Day"
                    elif day_type == "storm_days":
                        label = "Severe Storm Day"
                    elif day_type == "cold_days":
                        label = "Extreme Cold Day"
                    elif day_type == "covid_days":
                        label = "COVID-19 Closure"
                    elif day_type == "remote_days":
                        label = "Remote Learning Day"
                    elif day_type == "hybrid_days":
                        label = "Hybrid Learning Day"
                    break
            
            if not found_weather_day:
                # 5. FIFTH PRIORITY: Check if it's a teacher work day
                if current_date in teacher_work_days.get(school_year_id, []):
                    is_school_day = False
                    label = "Teacher Work Day"
                
                # 6. SIXTH PRIORITY: Check if it's a professional development day
                elif current_date in professional_dev_days.get(school_year_id, []):
                    is_school_day = False
                    label = "Professional Development Day"
                
                # 7. SEVENTH PRIORITY: Check if it's a testing day
                elif (current_date == testing_days[school_year_id]["psat_day"] or
                      current_date == testing_days[school_year_id]["sat_day"] or
                      current_date == testing_days[school_year_id]["graduation"] or
                      current_date in testing_days[school_year_id]["ap_weeks"]):
                    if current_date == testing_days[school_year_id]["psat_day"]:
                        label = "PSAT Day"
                        is_school_day = True
                    elif current_date == testing_days[school_year_id]["sat_day"]:
                        label = "SAT School Day"
                        is_school_day = True
                    elif current_date == testing_days[school_year_id]["graduation"]:
                        label = "Graduation Ceremony"
                        is_school_day = False
                    elif current_date in testing_days[school_year_id]["ap_weeks"]:
                        label = "AP Exam Week"
                        is_school_day = True
                
                # 8. EIGHTH PRIORITY: Check if it's a special event
                elif (current_date == special_events_by_year[school_year_id]["homecoming"] or
                      current_date == special_events_by_year[school_year_id]["field_day"] or
                      current_date in special_events_by_year[school_year_id]["spirit_week"]):
                    is_school_day = True
                    if current_date == special_events_by_year[school_year_id]["homecoming"]:
                        label = "Homecoming"
                    elif current_date in special_events_by_year[school_year_id]["spirit_week"]:
                        label = "Spirit Week"
                    elif current_date == special_events_by_year[school_year_id]["field_day"]:
                        label = "Field Day"
                
                # 9. NINTH PRIORITY: Check if it's Easter Monday
                elif current_date in special_events:
                    label = special_events[current_date]
                    is_school_day = False
                
                # 10. FINAL PRIORITY: Regular school day
                else:
                    is_school_day = True
                    label = "School Day"
        
        # Handle days outside school year
        elif school_year_id is None:
            label = "Summer Break"
            is_school_day = False
        
        # Default case for weekdays during school year
        elif current_date.weekday() < 5:
            is_school_day = True
            label = "School Day"
        
        # Create timestamp
        timestamp = datetime.combine(current_date, datetime.min.time())
        
        calendar_data.append({
            'calendar_date': current_date.strftime('%Y-%m-%d'),
            'school_year_id': school_year_id if school_year_id else '',
            'is_school_day': is_school_day,
            'is_holiday': is_holiday,
            'label': label,
            'created_at': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        current_date += timedelta(days=1)
    
    # Convert to DataFrame and save to CSV file
    df = pd.DataFrame(calendar_data)
    
    # Save to CSV file
    df.to_csv(output_file, index=False)
    
    # Print comprehensive statistics
    print(f"\n[SUCCESS] Successfully generated {len(calendar_data)} calendar entries")
    print(f"Date range: {calendar_data[0]['calendar_date']} to {calendar_data[-1]['calendar_date']}")
    print(f"Saved to: {os.path.abspath(output_file)}")
    
    # Enhanced validation statistics
    total_school_days = df['is_school_day'].sum()
    total_holidays = df['is_holiday'].sum() 
    total_weekends = len(df[df['label'].isin(['Saturday', 'Sunday'])])
    
    # Count specific day types
    weather_days = len(df[df['label'].str.contains('Snow Day|Ice Day|Storm Day|Cold Day', na=False)])
    covid_days = len(df[df['label'].str.contains('COVID|Remote|Hybrid', na=False)])
    teacher_days = len(df[df['label'].str.contains('Teacher Work Day|Professional Development', na=False)])
    testing_days = len(df[df['label'].str.contains('PSAT|SAT|AP Exam|Graduation', na=False)])
    special_events = len(df[df['label'].str.contains('Homecoming|Spirit|Field Day', na=False)])
    
    print(f"\nCOMPREHENSIVE VALIDATION SUMMARY:")
    print(f"   Total School Days: {total_school_days}")
    print(f"   Federal Holidays: {total_holidays}")
    print(f"   Weekend Days: {total_weekends}")
    print(f"   Weather/Emergency Days: {weather_days}")
    print(f"   COVID-related Days: {covid_days}")
    print(f"   Teacher Work/PD Days: {teacher_days}")
    print(f"   Testing Days: {testing_days}")
    print(f"   Special Events: {special_events}")
    
    # Count school days by year with detailed breakdown
    school_day_counts = df[df['school_year_id'] != ''].groupby('school_year_id')['is_school_day'].sum()
    print(f"\nSchool days per academic year:")
    for year_id, count in school_day_counts.items():
        year_label = f"{2015 + int(year_id)}-{2016 + int(year_id)}"
        year_df = df[df['school_year_id'] == str(year_id)]
        weather_count = len(year_df[year_df['label'].str.contains('Snow Day|Ice Day|Storm Day|Cold Day', na=False)])
        covid_count = len(year_df[year_df['label'].str.contains('COVID|Remote|Hybrid', na=False)])
        
        status = "[OK]" if 175 <= count <= 185 else "[WARN]"
        print(f"   {year_label}: {count} days {status} (Weather: {weather_count}, COVID: {covid_count})")
        
    # Verify ~180 days per year requirement
    avg_school_days = school_day_counts.mean()
    print(f"\nAverage school days per year: {avg_school_days:.1f}")
    if 175 <= avg_school_days <= 185:
        print("   [SUCCESS] MEETS ~180 day requirement")
    else:
        print("   [WARNING] Outside expected 175-185 day range")
    
    # Show breakdown by day type
    day_type_counts = df['label'].value_counts().head(15)
    print(f"\nTop 15 day types:")
    for day_type, count in day_type_counts.items():
        print(f"   {day_type}: {count}")
    
    # Show file size
    file_size = os.path.getsize(output_file)
    print(f"\nFile size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    # Validation checks
    weekend_school_days = df[(df['label'].isin(['Saturday', 'Sunday'])) & (df['is_school_day'] == True)]
    if len(weekend_school_days) > 0:
        print(f"\n[WARNING] Found {len(weekend_school_days)} weekend days marked as school days!")
    else:
        print(f"\n[SUCCESS] No weekends marked as school days")
    
    return df


# Execute the generator
if __name__ == "__main__":
    print("="*80)
    print("LUMINOSITY SCHOOL CALENDAR GENERATOR")
    print("="*80)
    
    try:
        df = generate_complete_calendar()
        
        # Show sample data
        print(f"\nSample data (first 10 rows):")
        print(df.head(10).to_string(index=False))
        
        print(f"\nSample data (last 5 rows):")
        print(df.tail(5).to_string(index=False))
        
        print(f"\n[SUCCESS] Calendar generation completed successfully!")
        print(f"Ready for import into Supabase database")
        
    except Exception as e:
        print(f"[ERROR] Error generating calendar: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)