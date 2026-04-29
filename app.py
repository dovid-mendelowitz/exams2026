import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

# הגדרות תצוגה
st.set_page_config(page_title="מערכת בחינות 2026", layout="centered")
st.markdown("""<style>body, .stApp {direction: rtl; text-align: right;}</style>""", unsafe_allow_html=True)

# חיבור מאובטח למסד הנתונים
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# ניהול שלבים
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- מסך מנהל כללי סודי ---
# אם מזינים בסמל מוסד "000000", נפתח הדשבורד שלך
def show_admin():
    st.title("👑 דשבורד ניהול רשת")
    res = supabase.table("school_reports").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        st.dataframe(df)
    if st.button("חזרה למסך רגיל"):
        st.session_state.step = 1
        st.rerun()

# --- שלב 1: פרטי מוסד ---
if st.session_state.step == 1:
    st.title("🛡️ שלב 1: הזדהות")
    with st.form("login"):
        s_id = st.text_input("סמל מוסד")
        s_name = st.text_input("שם המוסד")
        submitted = st.form_submit_button("המשך")
        if submitted:
            if s_id == "000000": # קוד כניסה למנהל על
                st.session_state.step = "admin"
                st.rerun()
            st.session_state.school_data = {"סמל": s_id, "שם": s_name}
            st.session_state.step = 2
            st.rerun()

# --- שלב 2: העלאה ושמירה ---
elif st.session_state.step == 2:
    st.title("📂 העלאת נתונים")
    st.write(f"מוסד: {st.session_state.school_data['שם']}")
    
    up_file = st.file_uploader("העלה אקסל מצבת תלמידים", type=['xlsx'])
    
    if up_file:
        # כאן תבוא לוגיקת הניתוח המלאה שכתבנו
        st.success("הקובץ נותח בהצלחה!")
        
        if st.button("🚀 שלח דוח סופי להנהלה"):
            data = {
                "school_id": st.session_state.school_data["סמל"],
                "school_name": st.session_state.school_data["שם"],
                "completed_exams": 150, # דוגמה לנתון מחושב
                "target_exams": 550
            }
            supabase.table("school_reports").upsert(data).execute()
            st.success("הנתונים נשמרו בענן!")

elif st.session_state.step == "admin":
    show_admin()
