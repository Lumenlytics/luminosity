import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

st.title("🏫 Luminosity School Dashboard")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Student overview
students = supabase.table("students").select("*").execute()
st.metric("Total Students", len(students.data))

# Quick stats
col1, col2, col3 = st.columns(3)
with col1:
    teachers = supabase.table("teachers").select("*").execute()
    st.metric("Teachers", len(teachers.data))
with col2:
    classes = supabase.table("classes").select("*").execute()
    st.metric("Classes", len(classes.data))
with col3:
    grades = supabase.table("grades").select("*", count="exact").execute()
    st.metric("Total Grades", f"{grades.count:,}")
