import streamlit as st
import pandas as pd
from supabase import create_client
import io
import msoffcrypto

# --- הגדרות דף ---
st.set_page_config(page_title="מערכת זינוק 2026", layout="wide")
st.markdown("""<style>body, .stApp {direction: rtl; text-align: right;}</style>""", unsafe_allow_html=True)

# --- חיבור ל-Supabase ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error("שגיאה בחיבור למסד הנתונים.")

# --- הגדרות מקצועות וקושי (מבוסס על המיקודים) ---
SUBJECTS_META = {
    "תנ\"ך": {"level": "בינוני", "info": "פרקי בחירה ושאלות נושא"},
    "היסטוריה": {"level": "קשה", "info": "שינון רחב של תהליכים"},
    "ספרות": {"level": "קל-בינוני", "info": "ניתוח יצירות ושירים"},
    "אזרחות": {"level": "קל", "info": "מושגי יסוד ודמוקרטיה"},
    "יהדות": {"level": "בינוני", "info": "הלכות שבת, כשרות ותפילה"},
    "תושב\"ע": {"level": "בינוני-קשה", "info": "מסלולי משנה או גמרא"}
}

# --- פונקציות טכניות ---

def load_excel_safely(uploaded_file, password=None):
    """פתיחת אקסל מוגן בסיסמה או רגיל"""
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
        st.error(f"שגיאה בקובץ: {e}")
        return None

def analyze_data(dict_st, dict_gr):
    """ניתוח מצבת תלמידים וציונים"""
    res = {"students": 0, "completed": 0}
    
    # ניתוח מצבת (תלמידים משובצים בלבד כיתות י-יב)
    if dict_st:
        for df in dict_st.values():
            df.columns = df.columns.astype(str).str.strip()
            c_col = next((c for c in df.columns if 'שכבה' in c or 'כיתת אם' in c), None)
            s_col = next((c for c in df.columns if 'סטטוס' in c), None)
            if c_col and s_col:
                mask = (df[c_col].astype(str).str.contains("י'|י''א|י''ב", na=False)) & \
                       (df[s_col].astype(str).str.strip() == 'משובץ')
                res["students"] += len(df[mask])

    # ניתוח ציונים (חורף תשפ"ו בלבד)
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
                    mask = (df['מועד'].astype(str).str.contains("1/2026|תשפ\"ו", na=False)) & \
                           (df['ציון סופי'].notna())
                    res["completed"] += len(df[mask])
    return res

# --- ניהול שלבים ---
if 'step' not in st.session_state: st.session_state.step = 1

# --- שלב 1: כניסה ---
if st.session_state.step == 1:
    st.title("🛡️ זינוק 2026 - כניסה")
    with st.form("login"):
        s_id = st.text_input("סמל מוסד")
        s_name = st.text_input("שם מוסד")
        if st.form_submit_button("התחבר"):
            if len(s_id) == 6 and s_name:
                st.session_state.school_id = s_id
                st.session_state.school_name = s_name
                st.session_state.step = 2
                st.rerun()

# --- שלב 2: הגדרות ואנשי קשר ---
elif st.session_state.step == 2:
    st.title(f"הגדרות מוסד: {st.session_state.school_name}")
    with st.form("school_setup"):
        col1, col2 = st.columns(2)
        circle = col1.selectbox("שיוך למעגל", [1, 2, 3, 4])
        recognition = col1.radio("הכרה", ["עם הכרה", "ללא הכרה"])
        finish_11 = col2.checkbox("האם המוסד מסיים בכיתה י\"א?")
        
        st.subheader("👤 איש קשר חובה")
        c1, c2, c3 = st.columns(3)
        c_name = c1.text_input("שם מלא")
        c_mail = c2.text_input("אימייל")
        c_phone = c3.text_input("טלפון נייד")
        
        if st.form_submit_button("שמור והמשך"):
            if c_name and c_mail and c_phone:
                # שמירה ל-Supabase
                school_data = {
                    "school_id": st.session_state.school_id,
                    "school_name": st.session_state.school_name,
                    "circle": circle,
                    "recognition": recognition
                }
                supabase.table("school_reports").upsert(school_data).execute()
                
                contact_data = {
                    "school_id": st.session_state.school_id,
                    "name": c_name, "email": c_mail, "phone": c_phone, "role": "מנהל/רכז"
                }
                supabase.table("school_contacts").insert(contact_data).execute()
                
                st.session_state.step = 3
                st.rerun()

# --- שלב 3: העלאת דוחות ---
elif st.session_state.step == 3:
    st.title("📂 העלאת דוחות (חלק ב')")
    pw_guess = f"{st.session_state.school_name[:2].capitalize()}{st.session_state.school_id}"
    st.info(f"הסיסמה המומלצת לקבצים: {pw_guess}")
    
    pw = st.text_input("הזן סיסמת אקסל:", type="password")
    
    f1 = st.file_uploader("1. דוח תלמידים (שיבוץ)", type=['xlsx'])
    f2 = st.file_uploader("2. דוח ציונים (חורף 2026)", type=['xlsx'])
    f3 = st.file_uploader("3. דוח אוכלוסיות (מעגלים)", type=['xlsx'])
    
    if f1 and f2 and f3:
        if st.button("בצע ניתוח נתונים"):
            d1 = load_excel_safely(f1, pw)
            d2 = load_excel_safely(f2, pw)
            if d1 and d2:
                st.session_state.stats = analyze_data(d1, d2)
                st.session_state.step = 4
                st.rerun()

# --- שלב 4: מטריצת אסטרטגיה ---
elif st.session_state.step == 4:
    st.title("📊 מטריצת אסטרטגיה ובחירת מסלול")
    stats = st.session_state.stats
    target = stats["students"] * 5.5
    
    c1, c2, c3 = st.columns(3)
    c1.metric("תלמידים", stats["students"])
    c2.metric("יעד אירועים (5.5)", f"{target:.1f}")
    c3.metric("בוצעו בחורף", stats["completed"])
    
    st.divider()
    st.subheader("💡 תכנון חלוקת עומס")
    st.write("ניתן לפצל את התלמידים בין 'חזקים' (יותר בחינות) ל'חלשים' (פחות בחינות).")
    
    # מטריצת מקצועות דינמית
    matrix = []
    for sub, meta in SUBJECTS_META.items():
        matrix.append({
            "מקצוע": sub, "רמת קושי": meta["level"], "מידע": meta["info"],
            "נבחנים בי\"א": False, "נבחנים בי\"ב": False
        })
    
    st.data_editor(pd.DataFrame(matrix), use_container_width=True)
    
    if st.button("סיום ושליחת דוח סופי"):
        st.success("הנתונים נשמרו. תודה על שיתוף הפעולה!")
