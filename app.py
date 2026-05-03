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

# --- נתוני עזר: קטגוריות מקצועות (גנרי) ---
SUBJECT_METADATA = {
    "מקצוע עיוני א'": {"level": "בינוני", "pages": "40", "desc": "כולל פרקי בחירה ושאלות נושא"},
    "מקצוע עיוני ב'": {"level": "קשה", "pages": "65", "desc": "חומר רחב ותהליכים מורכבים"},
    "מקצוע חברתי א'": {"level": "קל-בינוני", "pages": "30", "desc": "מושגי יסוד ומרכיבי משטר"},
    "מקצוע ספרותי א'": {"level": "קל", "pages": "25", "desc": "ניתוח יצירות ותוכן ספרותי"},
    "מקצוע הלכתי א'": {"level": "בינוני", "pages": "50", "desc": "הלכות והנחיות מעשיות"},
    "מקצוע הלכתי ב'": {"level": "בינוני-קשה", "pages": "55", "desc": "עיון במקורות ופרשנות"}
}

# --- פונקציות עיבוד נתונים ---

def load_excel_safely(uploaded_file, password=None):
    """טעינת קובץ אקסל עם תמיכה בסיסמה"""
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
        st.error(f"שגיאה בטעינת הקובץ: {e}")
        return None

def process_analysis(dict_st, dict_gr):
    """ניתוח מצבת תלמידים וציונים"""
    results = {"students": 0, "completed": 0, "special_ed": 0}
    
    if dict_st:
        for sheet in dict_st.values():
            sheet.columns = sheet.columns.astype(str).str.strip()
            c_col = next((c for c in sheet.columns if 'שכבה' in c or 'כיתת אם' in c), None)
            s_col = next((c for c in sheet.columns if 'סטטוס' in c), None)
            if c_col and s_col:
                mask = (sheet[c_col].astype(str).str.contains("י'|י''א|י''ב", na=False)) & \
                       (sheet[s_col].astype(str).str.strip() == 'משובץ')
                results["students"] += len(sheet[mask])

    if dict_gr:
        for sheet in dict_gr.values():
            header_row = -1
            for i in range(min(15, len(sheet))):
                if any("מועד" in str(v) for v in sheet.iloc[i]):
                    header_row = i
                    break
            if header_row != -1:
                sheet.columns = sheet.iloc[header_row].astype(str).str.strip()
                sheet = sheet.iloc[header_row+1:]
                if "מועד" in sheet.columns and "ציון סופי" in sheet.columns:
                    mask = (sheet['מועד'].astype(str).str.contains("חורף|1/2026", na=False)) & \
                           (sheet['ציון סופי'].notna())
                    results["completed"] += len(sheet[mask])
    return results

# --- ניהול שלבי האפליקציה ---
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- שלב 1: הזדהות ---
if st.session_state.step == 1:
    st.title("🛡️ מערכת זינוק 2026 - כניסה")
    with st.form("login"):
        s_id = st.text_input("סמל מוסד (6 ספרות)")
        s_name = st.text_input("שם המוסד")
        if st.form_submit_button("התחבר"):
            if len(s_id) == 6 and s_name:
                st.session_state.school_id = s_id
                st.session_state.school_name = s_name
                st.session_state.step = 2
                st.rerun()

# --- שלב 2: הגדרות מוסד ואנשי קשר ---
elif st.session_state.step == 2:
    st.title(f"הגדרות עבור: {st.session_state.school_name}")
    with st.form("setup"):
        col1, col2 = st.columns(2)
        circle = col1.selectbox("שיוך למעגל", [1, 2, 3, 4, 5])
        recog = col1.radio("סטטוס הכרה", ["מוסד מוכר", "מוסד שאינו מוכר"])
        scope = col2.radio("שכבת סיום", ["כיתה י\"א", "כיתה י\"ב"])
        
        st.subheader("👤 איש קשר (חובה)")
        c_name = st.text_input("שם מלא")
        c_mail = st.text_input("כתובת מייל")
        c_phone = st.text_input("טלפון נייד")
        
        if st.form_submit_button("שמור והמשך"):
            if c_name and c_mail and c_phone:
                if supabase:
                    supabase.table("school_reports").upsert({
                        "school_id": st.session_state.school_id,
                        "school_name": st.session_state.school_name,
                        "circle": circle,
                        "recognition": recog
                    }).execute()
                st.session_state.step = 3
                st.rerun()

# --- שלב 3: העלאת דוחות ---
elif st.session_state.step == 3:
    st.title("📂 העלאת דוחות")
    suggested_pw = f"{st.session_state.school_name[:2].capitalize()}{st.session_state.school_id}"
    st.info(f"הסיסמה האחידה שהוגדרה: {suggested_pw}")
    
    pw = st.text_input("הזן סיסמת אקסל:", type="password")
    f1 = st.file_uploader("1. דוח מצבת (שיבוץ)", type=['xlsx'])
    f2 = st.file_uploader("2. דוח ציונים (חורף 2026)", type=['xlsx'])
    f3 = st.file_uploader("3. דוח אוכלוסיות (מעגלים)", type=['xlsx'])
    
    if f1 and f2 and f3:
        if st.button("בצע ניתוח נתונים"):
            d1 = load_excel_safely(f1, pw)
            d2 = load_excel_safely(f2, pw)
            if d1 and d2:
                st.session_state.results = process_analysis(d1, d2)
                st.session_state.step = 4
                st.rerun()

# --- שלב 4: מטריצת אסטרטגיה ---
elif st.session_state.step == 4:
    res = st.session_state.results
    target = res["students"] * 5.5
    st.title("📊 דשבורד אסטרטגי")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("תלמידים משובצים", res["students"])
    m2.metric("יעד אירועים (5.5)", f"{target:.1f}")
    m3.metric("בוצעו בפועל", res["completed"])
    
    st.divider()
    st.subheader("📋 בחירת מסלולי היבחנות")
    
    matrix = []
    for sub, meta in SUBJECT_METADATA.items():
        matrix.append({
            "מקצוע": sub, "קושי": meta["level"], "דפים": meta["pages"], "סטטוס": "זמין במיקוד"
        })
    st.data_editor(pd.DataFrame(matrix), use_container_width=True)
    
    if st.button("שמור אסטרטגיה"):
        st.success("הנתונים נשמרו בהצלחה.")
