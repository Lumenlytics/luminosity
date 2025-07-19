import pandas as pd
import os

output_path = "data/clean_csv"
os.makedirs(output_path, exist_ok=True)

# Static rows for grade-level to class assignments
rows = [
    # Grade 9 (id = 9)
    {"grade_level_id": 9, "class_id": 101},  # Algebra I
    {"grade_level_id": 9, "class_id": 102},  # Biology
    {"grade_level_id": 9, "class_id": 103},  # PE
    {"grade_level_id": 9, "class_id": 104},  # English
    {"grade_level_id": 9, "class_id": 105},  # Geography
    {"grade_level_id": 9, "class_id": 106},  # Spanish I
    {"grade_level_id": 9, "class_id": 107},  # Computer Science

    # Grade 10
    {"grade_level_id": 10, "class_id": 201},  # Geometry
    {"grade_level_id": 10, "class_id": 202},  # Life Science
    {"grade_level_id": 10, "class_id": 203},  # PE
    {"grade_level_id": 10, "class_id": 204},  # American Literature
    {"grade_level_id": 10, "class_id": 205},  # Old World History
    {"grade_level_id": 10, "class_id": 206},  # Spanish II
    {"grade_level_id": 10, "class_id": 207},  # Visual Arts

    # Grade 11
    {"grade_level_id": 11, "class_id": 301},  # Algebra II
    {"grade_level_id": 11, "class_id": 302},  # Chemistry
    {"grade_level_id": 11, "class_id": 303},  # PE
    {"grade_level_id": 11, "class_id": 304},  # English Literature
    {"grade_level_id": 11, "class_id": 305},  # New World History
    {"grade_level_id": 11, "class_id": 306},  # Leadership
    {"grade_level_id": 11, "class_id": 307},  # Music Performance

    # Grade 12
    {"grade_level_id": 12, "class_id": 401},  # Calculus
    {"grade_level_id": 12, "class_id": 402},  # Psychology
    {"grade_level_id": 12, "class_id": 403},  # PE
    {"grade_level_id": 12, "class_id": 404},  # World Literature
    {"grade_level_id": 12, "class_id": 405},  # Government/Econ
    {"grade_level_id": 12, "class_id": 406},  # Leadership
]

df = pd.DataFrame(rows)
df.to_csv(os.path.join(output_path, "grade_level_class_map.csv"), index=False)
print("✅ grade_level_class_map.csv created.")
