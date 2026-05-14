from PIL import Image
import numpy as np
import streamlit as st
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import (
    get_all_students, create_student, get_student_subjects,
    get_student_attendance, unenroll_student_to_subject
)
from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card
from src.components.dialog_auto_enroll import auto_enroll_dialog
from src.ui.style_base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.database.config import supabase
import time


def student_dashboard():
    query_params = st.query_params
    subject_code = query_params.get("join-code")
    if subject_code:
        auto_enroll_dialog(subject_code)

    student_data = st.session_state.student_data
    student_id = student_data['student_id']

    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        header_dashboard()
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Go back", type='secondary', key='loginbackbtn', width='stretch'):
            st.session_state['is_logged_in'] = False
            if 'student_data' in st.session_state:
                del st.session_state.student_data
            st.rerun()

    st.space()

    # ── Welcome + Header ──────────────────────────────────────────────
    c1, c2 = st.columns([3, 1], vertical_alignment='center')
    with c1:
        st.header('Your Enrolled Subjects')
        st.caption(f"👋 Welcome, {student_data['name']}  |  🎓 Roll No: {student_data.get('roll_no', 'N/A')}  |  📚 Section: {student_data.get('section', 'N/A')}")
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()

    st.divider()

    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}
    for log in logs:
        sid = log['subject_id']
        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}
        stats_map[sid]['total'] += 1
        if log.get('is_present'):
            stats_map[sid]['attended'] += 1

    if not subjects:
        st.info("You are not enrolled in any subjects yet.")
        return

    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']
        stats = stats_map.get(sid, {"total": 0, "attended": 0})

        with cols[i % 2]:
            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=[
                    ('🗓️', 'Total', stats['total']),
                    ('✅', 'Attended', stats['attended']),
                ]
            )
            if st.button(
                "Unenroll from this subject",
                type='tertiary',
                use_container_width=True,
                key=f"unenroll_{sid}",
                icon=':material/delete_forever:'
            ):
                unenroll_student_to_subject(student_id, sid)
                st.toast(f"Unenrolled from {sub['name']} successfully!")
                time.sleep(1)
                st.rerun()


def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        header_dashboard()
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Go back", type='secondary', key='loginbackbtn', width='stretch'):
            st.session_state['login_type'] = None
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Toggle between Login and Register ─────────────────────────────
    if 'student_mode' not in st.session_state:
        st.session_state['student_mode'] = 'login'

    col1, col2 = st.columns(2)
    with col1:
        type1 = 'primary' if st.session_state['student_mode'] == 'login' else 'tertiary'
        if st.button('🔑 Login', type=type1, width='stretch'):
            st.session_state['student_mode'] = 'login'
            st.rerun()
    with col2:
        type2 = 'primary' if st.session_state['student_mode'] == 'register' else 'tertiary'
        if st.button('📝 Register', type=type2, width='stretch'):
            st.session_state['student_mode'] = 'register'
            st.rerun()

    st.divider()

    # ════════════════════════════════════════════════════════════════
    # LOGIN MODE — Name + Face only
    # ════════════════════════════════════════════════════════════════
    if st.session_state['student_mode'] == 'login':
        st.header('Login using faceID', text_alignment="left")

        # Name input first
        login_name = st.text_input(
            "Enter your name",
            placeholder="E.g. Bhumika Goyal",
            key="login_name"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Face photo
        photo_source = st.camera_input("📷 Position your face in the center")

        st.markdown("<br>", unsafe_allow_html=True)

        if photo_source:
            if st.button('🔍 Login', type='primary', width='stretch'):
                if not login_name:
                    st.warning('Please enter your name!')
                else:
                    img = np.array(Image.open(photo_source))
                    with st.spinner('AI is scanning your face..'):
                        detected, all_ids, num_faces = predict_attendance(img)

                        if num_faces == 0:
                            st.warning('Face not found')
                        elif num_faces > 1:
                            st.warning('Multiple faces found! Please ensure only one face is visible.')
                        else:
                            if detected:
                                student_id = list(detected.keys())[0]
                                all_students = get_all_students()

                                # Match by face AND name
                                student = next(
                                    (s for s in all_students
                                     if str(s['student_id']) == str(student_id)
                                     and s['name'].lower().strip() == login_name.lower().strip()),
                                    None
                                )
                                if student:
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = 'student'
                                    st.session_state.student_data = student
                                    st.toast(f"Welcome Back {student['name']}!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.warning('Name and face do not match. Please try again!')
                            else:
                                st.info('Face not recognized! Please register first.')
                                st.session_state['student_mode'] = 'register'
                                st.rerun()

    # ════════════════════════════════════════════════════════════════
    # REGISTER MODE — Name + Roll No + Section + Face + Voice
    # ════════════════════════════════════════════════════════════════
    elif st.session_state['student_mode'] == 'register':
        st.header('📝 Create New Profile')

        # ── Step 1: Personal Info ─────────────────────────────────
        with st.container(border=True):
            st.markdown("#### 👤 Step 1: Your Details")
            new_name = st.text_input(
                "Full Name",
                placeholder='E.g. Bhumika Goyal'
            )
            roll_no = st.text_input(
                "Enrollment / Roll Number",
                placeholder='E.g. 02601032024'
            )
            section = st.text_input(
                "Section",
                placeholder='E.g. IT-1'
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Step 2: Face Photo ────────────────────────────────────
        with st.container(border=True):
            st.markdown("#### 📷 Step 2: Take Your Photo")
            st.info("Position your face clearly in the center.")
            photo_source = st.camera_input("Take your photo", label_visibility='collapsed')
            if photo_source:
                st.success("✅ Photo captured!")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Step 3: Voice Recording ───────────────────────────────
        with st.container(border=True):
            st.markdown("#### 🎤 Step 3: Record Your Voice")
            st.info("Say 'I am present, my name is [your name]' clearly.")
            audio_data = None
            try:
                audio_data = st.audio_input("Record your voice", key="register_voice_input")
            except Exception:
                st.error("Audio input failed!")
            if audio_data:
                st.success("✅ Voice recorded!")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Create Account Button ─────────────────────────────────
        if st.button('🚀 Create Account', type='primary', width='stretch'):
            if not new_name:
                st.warning('Please enter your full name!')
            elif not roll_no:
                st.warning('Please enter your enrollment number!')
            elif not section:
                st.warning('Please enter your section!')
            elif not photo_source:
                st.warning('Please take your photo!')
            elif not audio_data:
                st.warning('Please record your voice!')
            else:
                with st.spinner('Creating your profile...'):
                    img = np.array(Image.open(photo_source))
                    encodings = get_face_embeddings(img)

                    if encodings:
                        face_emb = encodings[0].tolist()

                        voice_emb = None
                        with st.spinner('Processing voice...'):
                            voice_emb = get_voice_embedding(audio_data.read())

                        response_data = create_student(
                            new_name,
                            face_embedding=face_emb,
                            voice_embedding=voice_emb,
                            roll_no=roll_no,
                            section=section
                        )

                        if response_data:
                            train_classifier()
                            st.session_state.is_logged_in = True
                            st.session_state.user_role = 'student'
                            st.session_state.student_data = response_data[0]
                            st.session_state['student_mode'] = 'login'
                            st.toast(f'Profile Created! Hi {new_name}!')
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to create account. Please try again.")
                    else:
                        st.error("Couldn't capture your facial features. Please retake photo.")