import streamlit as st
import pandas as pd
from supabase import create_client
import io
import msoffcrypto

# --- הגדרות דף ---
st.set_page_config(page_title="מערכת זינוק 2026", layout="wide")
st.markdown("""
<style>
    body, .stApp { direction: rtl; text-align: right; }
    .stMetric { background-color: #f8fafc; padding: 15px; border-radius: 15px; border: 1px solid #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- חיבור למסד הנתונים (Supabase) ---
@st.cache_resource
def init_connection():
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except:
        return None

supabase = init_connection()

# --- פונקציות עיבוד נתונים ---
def load_excel_safely(uploaded_file, password=None):
    try:
        uploaded_file.seek(0)
        if password:
            try:
                office_file = msoffcrypto.OfficeFile(uploaded_file)
                office_file.load_key(password=password)
                decrypted = io.BytesIO()
                office_file.decrypt(decrypted)
                return pd.read_excel(decrypted, sheet_name=None)
            except:
                uploaded_file.seek(0)
                return pd.read_excel(uploaded_file, sheet_name=None)
        return pd.read_excel(uploaded_file, sheet_name=None)
    except Exception as e:
        return None

def analyze_data(dict_st, dict_gr):
    results = {"students": 0, "completed": 0}
    if dict_st:
        for df in dict_st.values():
            df.columns = df.columns.astype(str).str.strip()
            c_col = next((c for c in df.columns if 'שכבה' in c or 'כיתת אם' in c), None)
            s_col = next((c for c in df.columns if 'סטטוס' in c), None)
            if c_col and s_col:
                mask = (df[c_col].astype(str).str.contains("י'|י''א|י''ב", na=False)) & (df[s_col].astype(str).str.strip() == 'משובץ')
                results["students"] += len(df[mask])
    if dict_gr:
        for df in dict_gr.values():
            header_row = -1
            for i in range(min(15, len(df))):
                if any("מועד" in str(val) for val in df.iloc[i]):
                    header_row = i
                    break
            if header_row != -1:
                df.columns = df.iloc[header_row].astype(str).str.strip()
                df = df.iloc[header_row+1:]
                if "מועד" in df.columns and "ציון סופי" in df.columns:
                    mask = (df['מועד'].astype(str).str.contains("1/2026|תשפ\"ו", na=False)) & (df['ציון סופי'].notna())
                    results["completed"] += len(df[mask])
    return results

# --- ניהול שלבים ---
if 'step' not in st.session_state: st.session_state.step = 1

# שלב 1: כניסה (כולל לוגיקת מנהל)
if st.session_state.step == 1:
    st.title("🛡️ מערכת זינוק 2026 - כניסה")
    with st.form("login"):
        s_id = st.text_input("סמל מוסד (6 ספרות)")
        s_name = st.text_input("שם המוסד")
        
        # בדיקה האם המשתמש מנסה להיכנס כמנהל
        admin_pass = ""
        if s_id == "000000":
            admin_pass = st.text_input("סיסמת מנהל מערכת", type="password")
            
        if st.form_submit_button("התחבר"):
            if s_id == "000000":
                # בדיקת סיסמה מול ה-Secrets של Streamlit
                if admin_pass == st.secrets.get("ADMIN_PASSWORD", "1234"):
                    st.session_state.step = "admin"
                    st.rerun()
                else:
                    st.error("סיסמת מנהל שגויה")
            elif len(s_id) == 6 and s_name:
                st.session_state.school_id = s_id
                st.session_state.school_name = s_name
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("נא למלא סמל מוסד תקין")

# שלב אדמין: דשבורד מרכזי
elif st.session_state.step == "admin":
    st.title("👑 דשבורד מנהל רשת - ריכוז נתונים")
    if st.button("התנתק"):
        st.session_state.step = 1
        st.rerun()
        
    res = supabase.table("school_reports").select("*").execute()
    if res.data:
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
    else:
        st.info("אין עדיין דיווחים במערכת.")

# שלב 2: הגדרות מוסד (למשתמש רגיל)
elif st.session_state.step == 2:
    st.title(f"הגדרות עבור: {st.session_state.school_name}")
    with st.form("setup"):
        col1, col2 = st.columns(2)
        circle = col1.selectbox("שיוך למעגל", [1, 2, 3, 4, 5])
        recog = col1.radio("סטטוס הכרה", ["עם הכרה", "ללא הכרה"])
        c_name = st.text_input("שם איש קשר")
        c_mail = st.text_input("אימייל")
        c_phone = st.text_input("טלפון")
        if st.form_submit_button("שמור והמשך"):
            if c_name and c_mail and c_phone:
                supabase.table("school_reports").upsert({
                    "school_id": st.session_state.school_id, "school_name": st.session_state.school_name,
                    "circle": circle, "recognition": recog
                }).execute()
                st.session_state.step = 3
                st.rerun()

# שלב 3: העלאת דוחות
elif st.session_state.step == 3:
    st.title("📂 העלאת דוחות")
    pw = st.text_input("סיסמת אקסל:", type="password")
    f1 = st.file_uploader("1. דוח מצבת", type=['xlsx'])
    f2 = st.file_uploader("2. דוח ציונים", type=['xlsx'])
    f3 = st.file_uploader("3. דוח אוכלוסיות", type=['xlsx'])
    if f1 and f2 and f3:
        if st.button("ניתוח נתונים"):
            d1 = load_excel_safely(f1, pw); d2 = load_excel_safely(f2, pw)
            if d1 and d2:
                st.session_state.stats = analyze_data(d1, d2)
                st.session_state.step = 4
                st.rerun()

# שלב 4: תוצאות
elif st.session_state.step == 4:
    st.title("📊 תוצאות")
    st.write(f"תלמידים: {st.session_state.stats['students']}")
    if st.button("חזרה"):
        st.session_state.step = 1
        st.rerun()
