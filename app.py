import streamlit as st
import pandas as pd

# הגדרות תצוגה לעברית
st.set_page_config(page_title="מערכת בחינות 2026", layout="centered")
st.markdown("""<style>body, .stApp {direction: rtl; text-align: right; font-family: 'Arial';}</style>""", unsafe_allow_html=True)

# ניהול מצב המערכת (States)
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- מסך 1: הזדהות ופרטי מוסד ---
if st.session_state.step == 1:
    st.title("🛡️ שלב 1: הזדהות ופרטי מוסד")
    st.write("ברוכים הבאים למערכת ניהול הבחינות. אנא מלאו את פרטי המוסד המדויקים.")
    
    with st.form("school_info"):
        school_name = st.text_input("שם המוסד")
        school_id = st.text_input("סמל מוסד (6 ספרות)")
        contact_name = st.text_input("שם איש קשר")
        contact_phone = st.text_input("טלפון ליצירת קשר")
        
        circle = st.selectbox("מספר מעגל (לפי מפת ההקלות)", [1, 2, 3])
        recognition = st.radio("האם למוסד יש הכרה בציונים?", ["יש הכרה", "אין הכרה"])
        
        submitted = st.form_submit_button("המשך לשלב הבא ➔")
        if submitted:
            if school_name and school_id:
                st.session_state.school_data = {
                    "שם": school_name, "סמל": school_id, "מעגל": circle, "הכרה": recognition
                }
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("אנא מלאו שם וסמל מוסד כדי להמשיך.")

# --- מסך 2: הדרכה והעלאת קבצים ---
elif st.session_state.step == 2:
    st.title("📂 שלב 2: העלאת דוחות")
    st.info(f"מוסד: {st.session_state.school_data['שם']} | מעגל: {st.session_state.school_data['מעגל']}")
    
    st.write("""
    **הנחיות להורדת הקבצים מהפורטל:**
    1. הורידו את דוח **'מצבת תלמידים'** (פורמט אקסל).
    2. הורידו את דוח **'ציוני נבחנים'** או **'שיוך שאלונים'** (שנת 2025).
    3. וודאו שהקבצים נשארים בפורמט המקורי ללא שינוי עמודות.
    """)
    
    st.divider()
    
    student_file = st.file_uploader("העלה אקסל מצבת תלמידים", type=['xlsx'])
    grades_file = st.file_uploader("העלה אקסל ציונים/שיוכים", type=['xlsx'])
    
    if student_file and grades_file:
        st.success("✅ הקבצים התקבלו בהצלחה!")
        st.write("המערכת כעת בתקופת הרצה. הנתונים נשלחים לבדיקה טכנית.")
        
        # כאן בעתיד יבוא מנוע הניתוח
        if st.button("סיום ושליחה"):
            st.balloons()
            st.write("תודה! הנתונים נקלטו. המערכת תעבד אותם ותחזור אליך עם המלצות.")
            
    if st.button("⬅️ חזרה לתיקון פרטים"):
        st.session_state.step = 1
        st.rerun()