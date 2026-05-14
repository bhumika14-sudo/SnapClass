import streamlit as st
from src.database.config import supabase
import time 
from src.database.db import create_attendance

def show_attendance_result(df, logs, result_key='voice_attendance_results'):
    st.write('Please review attendance before confirming.')
    st.dataframe(df, hide_index=True, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button('Discard', width='stretch', type='secondary'):
            st.session_state[result_key] = None
            st.session_state.attendance_images = []
            st.rerun()

    with col2:
        if st.button('Confirm & Save', width='stretch', type='primary'):
            try:
                create_attendance(logs)
                st.toast('✅ Attendance saved successfully!')
                st.session_state.attendance_images = []
                st.session_state[result_key] = None
                st.rerun()
            except Exception as e:
                st.error(f'Sync failed: {e}')

@st.dialog("Attendance Report")
def attendance_result_dialog(df, logs):
    show_attendance_result(df, logs, result_key='face_attendance_results')

@st.dialog("Attendance Report")
def voice_attendance_result_dialog(df, logs):
    show_attendance_result(df, logs, result_key='voice_attendance_results')