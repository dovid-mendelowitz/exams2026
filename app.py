import streamlit as st
import pandas as pd
from supabase import create_client
import io
import msoffcrypto

# --- הגדרות דף ---
st.set_page_config(page_title="מערכת ניהול בחינות 2026", layout="wide")
st.markdown("""<style>body, .stApp {direction: rtl; text-align: right;}</style>""", unsafe_allow_html=True)

# --- חיבור לענן (Supabase) ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error("שגיאה בחיבור למסד הנתונים. ודא שהגדרת את ה-Secrets כראוי.")

# --- רשימת 19 המקצועות לפי סדר המיון שלך ---
SUBJECTS_ORDER = [
    "תנ\"ך - עצמאי", "תנ\"ך עצמאי הגבר", "יהדות עצמאי", "יהדות עצמאי תניא", 
    "יהדות עצמאי הגבר", "תושב\"ע חמ\"ד", "תושב\"ע חמ\"ד הגבר 5 יח\"ל",
    "תלמוד חמ\"ד רגיל/עולה", "תלמוד חמ\"ד הגבר 5 יח\"ל רגיל/עולה", 
    "תלמוד חמ\"ד הגבר 5 יח\"ל", "ספרות- לבי\"ס עצמאי", 
    "ספרות עצמאי הגבר 5 יח\"ל רגיל/עולה", "עברית עצמאי", 
    "היסטוריה עצמאי", "אזרחות", "אנגלית 3 יח\"ל רגיל", 
    "אנגלית 3 יח\"ל ללא הכרה", "מתמטיקה 3 יח\"ל", "מתמטיקה 3 יח\"ל תוכנית חדשה"
]

# --- פונקציות עזר לניתוח ---

def load_excel_safely(uploaded_file, password=None):
    """טוען אקסל גם אם הוא מוגן בסיסמה בעזרת msoffcrypto"""
    try:
        if password:
            office_file = msoffcrypto.OfficeFile(uploaded_file)
            office_file.load_key(password=password)
            decrypted = io.BytesIO()
            office_file.decrypt(decrypted)
            return pd.read_excel(decrypted)
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"לא ניתן לפתוח את הקובץ. ודא שהסיסמה נכונה. שגיאה: {e}")
        return None

def process_data(df_st, df_gr):
    """מנתח את מצבת התלמידים והציונים"""
    mask = df_st['שכבה/ כיתת אם'].astype(str).str.contains("י'|י''א|י''ב", na=False)
    student_count = len(df_st[mask])
    target = student_count * 5.5
    
    done_count = 0
    if df_gr is not None:
        if "שנת לימודים" not in df_gr.columns:
            df_gr.columns = df_gr.iloc[3]
            df_gr = df_gr[4:].reset_index(drop=True)
        
        current_exams = df_gr[df_gr['שנת לימודים'].astype(str).str.contains("2026", na=False)]
        done_count = len(current_exams)
        
    return student_count, target, done_count

# --- ניהול שלבי האפליקציה ---
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- שלב 1: מסך כניסה ---
if st.session_state.step == 1:
    st.title("🛡️ מערכת זינוק 2026 - כניסה מאובטחת")
    with st.form("login"):
        s_id = st.text_input("סמל מוסד")
        s_name = st.text_input("שם המוסד")
        
        admin_pass = ""
        if s_id == "000000":
            admin_pass = st.text_input("סיסמת מנהל רשת", type="password")
            
        if st.form_submit_button("התחבר"):
            if s_id == "000000":
                if admin_pass == st.secrets["ADMIN_PASSWORD"]:
                    st.session_state.step = "admin"
                    st.rerun()
                else:
                    st.error("סיסמת מנהל שגויה!")
            elif s_id and s_name:
                st.session_state.school_data = {"id": s_id, "name": s_name}
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("נא למלא את כל השדות")

# --- שלב 2: העלאאת קבצים וניתוח ---
elif st.session_state.step == 2:
    st.title(f"שלום, מוסד {st.session_state.school_data['name']}")
    st.subheader("העלאת דוחות משרד החינוך")
    
    excel_p = st.text_input("אם קבצי האקסל מוגנים בסיסמה, הזן אותה כאן (אחרת השאר ריק):", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        st_file = st.file_uploader("1. העלה מצבת תלמידים (XLSX)", type=['xlsx'])
    with col2:
        gr_file = st.file_uploader("2. העלה קובץ ציונים/שאלונים (XLSX)", type=['xlsx'])
    
    if st_file:
        df_st = load_excel_safely(st_file, excel_p)
        df_gr = load_excel_safely(gr_file, excel_p) if gr_file else None
        
        if df_st is not None:
            s_count, target, done = process_data(df_st, df_gr)
            
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("תלמידים (י-יב)", s_count)
            m2.metric("יעד אירועי בחינה", f"{target:.1f}")
            m3.metric("בוצעו בפועל (2026)", done)
            
            if st.button("🚀 שלח דיווח סופי למנהל הרשת"):
                report = {
                    "school_id": st.session_state.school_data["id"],
                    "school_name": st.session_state.school_data["name"],
                    "total_students": s_count,
                    "target_exams": float(target),
                    "completed_exams": done
                }
                supabase.table("school_reports").upsert(report).execute()
                st.success("הנתונים נשמרו בהצלחה!")

# --- שלב אדמין: דשבורד מנהל רשת ---
elif st.session_state.step == "admin":
    st.title("👑 דשבורד מנהל רשת - תמונת מצב")
    
    res = supabase.table("school_reports").select("*").execute()
    if res.data:
        full_df = pd.DataFrame(res.data)
        st.dataframe(full_df, use_container_width=True)
    else:
        st.info("אין עדיין דיווחים מהמוסדות.")
        
    if st.button("יציאה מהמערכת"):
        st.session_state.step = 1
        st.rerun()
