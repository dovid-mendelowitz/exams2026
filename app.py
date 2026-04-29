import streamlit as st
import pandas as pd
from supabase import create_client
import datetime

# הגדרות בסיסיות
st.set_page_config(page_title="מערכת בחינות 2026", layout="wide")
st.markdown("""<style>body, .stApp {direction: rtl; text-align: right;}</style>""", unsafe_allow_html=True)

# חיבור ל-Supabase דרך ה-Secrets
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

if 'step' not in st.session_state:
    st.session_state.step = 1

# --- פונקציית דשבורד מנהל כללי ---
def show_admin_dashboard():
    st.title("👑 דשבורד מנהל כללי - תמונת מצב רשתית")
    try:
        res = supabase.table("school_reports").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['אחוז ביצוע'] = (df['completed_exams'] / df['target_exams'] * 100).round(1)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("טרם התקבלו דיווחים מהמוסדות.")
    except Exception as e:
        st.error(f"שגיאה במשיכת נתונים: {e}")
    
    if st.button("חזרה למסך ראשי"):
        st.session_state.step = 1
        st.rerun()

# --- שלב 1: הזדהות ---
if st.session_state.step == 1:
    st.title("🛡️ מערכת ניהול בחינות 2026 - כניסה")
    with st.form("login"):
        school_id = st.text_input("סמל מוסד")
        school_name = st.text_input("שם המוסד")
        submitted = st.form_submit_button("המשך")
        
        if submitted:
            if school_id == "000000": # קוד סודי עבורך
                st.session_state.step = "admin"
                st.rerun()
            elif school_id and school_name:
                st.session_state.school_data = {"סמל": school_id, "שם": school_name}
                st.session_state.step = 2
                st.rerun()

# --- שלב 2: ניתוח ושמירה ---
elif st.session_state.step == 2:
    st.title(f"📂 ניתוח נתונים: {st.session_state.school_data['שם']}")
    
    # כאן המנהל יעלה את הקבצים (כרגע סימולציה של שמירה)
    st.info("כאן המערכת תבצע את ניתוח האקסלים שהעלית.")
    
    # כפתור דיווח להנהלה
    if st.button("🚀 סיים ודווח להנהלה"):
        data = {
            "school_id": st.session_state.school_data["סמל"],
            "school_name": st.session_state.school_data["שם"],
            "completed_exams": 100, # נתון שיחושב מהאקסל
            "target_exams": 550,   # נתון שיחושב מהאקסל
        }
        try:
            supabase.table("school_reports").upsert(data).execute()
            st.success("הנתונים נשמרו בהצלחה בדשבורד המנהל הכללי!")
        except Exception as e:
            st.error(f"שגיאה בשמירה: {e}")

elif st.session_state.step == "admin":
    show_admin_dashboard()
