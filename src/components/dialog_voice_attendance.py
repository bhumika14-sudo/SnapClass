import streamlit as st
from src.pipelines.voice_pipeline import process_bulk_audio 
from src.database.config import supabase
from src.database.db import create_attendance
from datetime import datetime 
import pandas as pd

@st.dialog('Voice Attendance')
def voice_attendance_dialog(selected_subject_id):
    st.write('Record audio of students saying "I am Present". Then AI will recognize the students.')
    
    audio_data = st.audio_input("Record classroom audio") 

    if st.button('Analyze Audio', width='stretch', type='primary'):
        if not audio_data:
            st.warning('Please record audio first')
            return

        with st.spinner('Processing Audio data...'):
            enrolled_res = supabase.table('subject_students')\
                .select("*, students(*)")\
                .eq('subject_id', selected_subject_id)\
                .execute()
            enrolled_students = enrolled_res.data

            if not enrolled_students:
                st.warning('No students enrolled in this course')
                return 
            
            candidates_dict = {
                s['students']['student_id']: s['students']['voice_embedding']
                for s in enrolled_students 
                if s['students'] and s['students'].get('voice_embedding')  
            }

            if not candidates_dict:
                st.error('No enrolled students have voice profiles registered')
                return 

            audio_bytes = audio_data.read()
            detected_scores = process_bulk_audio(audio_bytes, candidates_dict)

            results, attendance_to_log = [], []
            current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            for node in enrolled_students:
                student = node['students']
                score = detected_scores.get(student['student_id'], 0)
                is_present = bool(score > 0)

                results.append({
                    "Name": student['name'],
                    "ID": student['student_id'],
                    "Score": round(score, 4) if is_present else "-",
                    "Status": "✅ Present" if is_present else "❌ Absent"
                })

                attendance_to_log.append({
                    'student_id': student['student_id'],
                    'subject_id': selected_subject_id,
                    'timestamp': current_timestamp,
                    'is_present': bool(is_present)
                })

            # Store in session state to show below
            st.session_state['_voice_results'] = pd.DataFrame(results)
            st.session_state['_voice_logs'] = attendance_to_log

    # Show results inside the same dialog
    if st.session_state.get('_voice_results') is not None:
        st.divider()
        st.write('Please review attendance before confirming.')
        st.dataframe(
            st.session_state['_voice_results'], 
            hide_index=True, 
            use_container_width=True
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button('Discard', width='stretch', type='secondary'):
                st.session_state['_voice_results'] = None
                st.session_state['_voice_logs'] = None
                st.rerun()
        with col2:
            if st.button('Confirm & Save', width='stretch', type='primary'):
                try:
                    create_attendance(st.session_state['_voice_logs'])
                    st.toast('✅ Attendance saved successfully!')
                    st.session_state['_voice_results'] = None
                    st.session_state['_voice_logs'] = None
                    st.rerun()
                except Exception as e:
                    st.error(f'Save failed: {e}')