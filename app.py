import streamlit as st
import pandas as pd
from supabase import create_client
import datetime

# --- הגדרות ליבה ורשימת מקצועות (המיון שלך) ---
SUBJECTS_ORDER = [
    "תנ\"ך - עצמאי", "תנ\"ך עצמאי הגבר", "יהדות עצמאי", "יהדות עצמאי תניא", 
    "יהדות עצמאי הגבר", "תושב\"ע חמ\"ד", "תושב\"ע חמ\"ד הגבר 5 יח\"ל",
    "תלמוד חמ\"ד רגיל/עולה", "תלמוד חמ\"ד הגבר 5 יח\"ל רגיל/עולה", 
    "תלמוד חמ\"ד הגבר 5 יח\"ל", "ספרות- לבי\"ס עצמאי", 
    "ספרות עצמאי הגבר 5 יח\"ל רגיל/עולה", "עברית עצמאי", 
    "היסטוריה עצמאי", "אזרחות", "אנגלית 3 יח\"ל רגיל", 
    "אנגלית 3 יח\"ל ללא הכרה", "מתמטיקה 3 יח\"ל", "מתמטיקה 3 יח\"ל תוכנית חדשה"
]

st.set_page_config(page_title="ניהול בחינות 2026", layout="wide")
st.markdown("""<style>body, .stApp {direction: rtl; text-align: right;}</style>""", unsafe_allow_html=True)

# חיבור לענן
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

if 'step' not in st.session_state:
    st.session_state.step = 1

# --- פונקציית ניתוח קבצים (המוח) ---
def process_files(student_file, grades_file):
    # כאן נכנסת הלוגיקה של דילוג 3 שורות וזיהוי שנתונים
    df_students = pd.read_excel(student_file)
    # ספירת תלמידים י-יב
    count = len(df_students[df_students['שכבה/ כיתת אם'].str.contains("י'|י''א|י''ב", na=False)])
    target = count * 5.5
    return count, target

# --- מסך מנהל כללי ---
def show_admin_dashboard():
    st.title("👑 דשבורד מנהל כללי")
    res = supabase.table("school_reports").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        st.write("תמונת מצב רשתית:")
        st.dataframe(df)
    if st.button("יציאה"):
        st.session_state.step = 1
        st.rerun()

# --- שלב 1: כניסה ---
if st.session_state.step == 1:
    st.title("🛡️ כניסה למערכת")
    with st.form("login_form"):
        s_id = st.text_input("סמל מוסד")
        s_name = st.text_input("שם המוסד")
        if s_id == "000000":
            password = st.text_input("סיסמת מנהל", type="password")
        
        submitted = st.form_submit_button("התחבר")
        if submitted:
            if s_id == "000000":
                if password == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state.step = "admin"
                    st.rerun()
                else:
                    st.error("סיסמה שגויה")
            else:
                st.session_state.school_data = {"סמל": s_id, "שם": s_name}
                st.session_state.step = 2
                st.rerun()

# --- שלב 2: העלאה וניתוח ---
elif st.session_state.step == 2:
    st.header(f"שלום למוסד: {st.session_state.school_data['שם']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st_file = st.file_uploader("העלה מצבת תלמידים", type=['xlsx'])
    with col2:
        gr_file = st.file_uploader("העלה ציוני חורף (אופציונלי)", type=['xlsx'])
    
    if st_file:
        count, target = process_files(st_file, gr_file)
        st.metric("סה\"כ תלמידים (י-יב)", count)
        st.metric("יעד אירועי בחינה", target)
        
        if st.button("🚀 דווח סופי להנהלה"):
            data = {
                "school_id": st.session_state.school_data["סמל"],
                "school_name": st.session_state.school_data["שם"],
                "total_students": count,
                "target_exams": target
            }
            supabase.table("school_reports").upsert(data).execute()
            st.success("דווח בהצלחה!")

elif st.session_state.step == "admin":
    show_admin_dashboard()
