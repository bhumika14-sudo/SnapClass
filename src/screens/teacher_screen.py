import streamlit as st
from src.ui.style_base_layout import style_background_dashboard, style_base_layout
import numpy as np
import pandas as pd
from src.components.header import header_dashboard
from src.database.db import check_teacher_exists, create_teacher, teacher_login, get_teacher_subject, get_attendance_for_teacher
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.subject_card import subject_card
from src.components.dialog_add_photo import add_photos_dialog
from src.pipelines.face_pipeline import predict_attendance
from src.components.dialog_attendance_results import attendance_result_dialog
from src.database.config import supabase
from datetime import datetime
from src.components.dialog_voice_attendance import voice_attendance_dialog
import time

if "attendance_images" not in st.session_state:
    st.session_state["attendance_images"] = []

def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type == "login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()

def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        header_dashboard()
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Go back", type='secondary', key='loginbackbtn', use_container_width=True):  # fix 4
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data
            st.rerun()

    st.divider()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"

    tab1, tab2, tab3 = st.columns(3)
    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else 'secondary'  # fix 3
        if st.button('Take Attendance', type=type1, use_container_width=True, icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()
    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else 'secondary'  # fix 3
        if st.button('Manage Subjects', type=type2, use_container_width=True, icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()
    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_records' else 'secondary'  # fix 3
        if st.button('Attendance Records', type=type3, use_container_width=True, icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_records'
            st.rerun()

    st.divider()

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()


def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendance')

    if "attendance_images" not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subject(teacher_id)
    if not subjects:
        st.warning('You haven\'t created any subject yet! Please create one to begin!')
        return

    subject_options = {f"{s['name']} - {s['section']}": s['subject_id'] for s in subjects}

    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')
    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))
    with col2:
        if st.button('Add Photos', type='primary', icon=':material/photo_auto_merge:', use_container_width=True):  # fix 4
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    if st.session_state.get("attendance_images", []):
        st.header('Added Photos')
        gallery_cols = st.columns(4)
        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, use_container_width=True, caption=f'Photo {idx+1}')  # fix 4

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Clear All Photos", type="secondary", use_container_width=True, icon=":material/delete:"):  # fix 3, fix 4
            st.session_state["attendance_images"] = []
            st.session_state.pop("dialog_upload", None)
            st.session_state.pop("dialog_cam", None)
            st.session_state["last_camera_photo"] = None
            st.success("Photos cleared")
            st.rerun()

    with c2:
        if st.button('Run Face Analysis', use_container_width=True, type='secondary',  # fix 4
                     icon=':material/analytics:',
                     disabled=not bool(st.session_state.get("attendance_images", []))):

            all_detected_ids = {}
            with st.spinner('Deep scanning classroom photos...'):
                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    detected, _, _ = predict_attendance(img_np)
                    # fix 7: removed debug st.write statements
                    if detected:
                        for sid in detected.keys():
                            student_id = str(sid)
                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx+1}")

                enrolled_res = supabase.table('subject_students')\
                    .select("*")\
                    .eq('subject_id', selected_subject_id)\
                    .execute()

                enrolled_students = []
                for row in enrolled_res.data:
                    student_res = supabase.table("students").select("*").eq("student_id", row["student_id"]).execute()
                    if student_res.data:
                        enrolled_students.append({"students": student_res.data[0]})

                if not enrolled_students:
                    st.warning('No students enrolled in this course')
                else:
                    results, attendance_to_log = [], []
                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                    for node in enrolled_students:
                        student = node['students']
                        face_label = str(student['student_id'])
                        sources = all_detected_ids.get(face_label, [])
                        is_present = len(sources) > 0

                        results.append({
                            "Name": student['name'],
                            "ID": student['student_id'],
                            "Source": ", ".join(sources) if is_present else "-",
                            "Status": "✅ Present" if is_present else "❌ Absent"
                        })
                        attendance_to_log.append({
                            'student_id': student['student_id'],
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': bool(is_present)
                        })

                    # fix 1: store results in session_state, open dialog outside spinner
                    st.session_state['face_attendance_results'] = (pd.DataFrame(results), attendance_to_log)

        # fix 1: open dialog outside spinner on next rerun
        if st.session_state.get('face_attendance_results'):
            df, logs = st.session_state['face_attendance_results']
            attendance_result_dialog(df, logs)

    with c3:
        if st.button('Use Voice Attendance', type='primary', use_container_width=True, icon=':material/mic:'):  # fix 4
            voice_attendance_dialog(selected_subject_id)


def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2 = st.columns(2)
    with col1:
        st.header('Manage Subjects')
    with col2:
        if st.button('Create New Subject', use_container_width=True):  # fix 4
            create_subject_dialog(teacher_id)

    subjects = get_teacher_subject(teacher_id)
    if subjects:
        for sub in subjects:  # fix 5: everything inside the loop
            stats = [
                ("👨‍🎓", "Students", sub['total_students']),
                ("📚", "Classes", sub['total_classes'])
            ]

            def share_btn(sub=sub):  # fix 5: inside loop, default arg to capture sub
                if st.button(f"Share Code: {sub['name']}", key=f"share_{sub['subject_code']}", icon=":material/share:"):
                    share_subject_dialog(sub['name'], sub['subject_code'])
                st.write("")

            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=stats,
                footer_callback=share_btn
            )
    else:
        st.info("No subjects found — create one above.")


def teacher_tab_attendance_records():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Attendance Records')

    records = get_attendance_for_teacher(teacher_id)
    if not records:
        return

    data = []
    for r in records:
        ts = r.get('timestamp')
        data.append({
            "ts_group": ts.split(".")[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%y-%m-%d %I:%M %p") if ts else "N/A",
            "Subject": r['subjects']['name'],
            "Subject Code": r['subjects']['subject_code'],
            "is_present": bool(r.get('is_present', False))
        })

    df = pd.DataFrame(data)
    summary = (
        df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code'])
        .agg(Present_Count=('is_present', 'sum'), Total_Count=('is_present', 'count'))
        .reset_index()
    )
    summary['Attendance Stats'] = (
        "✅ " + summary['Present_Count'].astype(str) + " / "
        + summary['Total_Count'].astype(str) + " Students"
    )
    display_df = summary.sort_values(by='ts_group', ascending=False)[['Time', 'Subject', 'Subject Code', 'Attendance Stats']]
    st.dataframe(display_df, use_container_width=True, hide_index=True)  # fix 4


def login_teacher(username, password):
    if not username or not password:
        return False
    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.user_role = 'teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True
    return False


def teacher_screen_login():
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        header_dashboard()
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Go back", type='secondary', key='loginbackbtn', use_container_width=True):  # fix 4
            st.session_state['login_type'] = None
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.header('Login using password', anchor=False)
    st.markdown("<br>", unsafe_allow_html=True)

    teacher_username = st.text_input("Enter username", placeholder="Bhumika")
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password")
    st.markdown("<br>", unsafe_allow_html=True)

    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button('Login', icon=':material/passkey:', use_container_width=True):  # fix 4
            if login_teacher(teacher_username, teacher_pass):
                st.success("👋 Welcome back!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username or password")
    with btnc2:
        if st.button('Register Instead', type="primary", icon=':material/person_add:', use_container_width=True):  # fix 4
            st.session_state.teacher_login_type = 'register'
            st.rerun()


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_pass:
        return False, "All fields are required!"
    if check_teacher_exists(teacher_username):
        return False, "Username already taken"
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords do not match"
    try:
        create_teacher(teacher_username, teacher_pass, teacher_name)
        return True, "Successfully created! Login now."
    except Exception as e:
        return False, f"Unexpected error: {e}"


def teacher_screen_register():
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        header_dashboard()
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Go back", type='secondary', key='registerbackbtn', use_container_width=True):  # fix 4
            st.session_state['login_type'] = None  # fix 6: was 'Login_type'
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.header('Register your teacher profile', anchor=False)
    st.markdown("<br>", unsafe_allow_html=True)

    teacher_name = st.text_input("Enter name", placeholder="Bhumika Goyal")
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    teacher_username = st.text_input("Enter username", placeholder="bhumika123")
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    teacher_pass = st.text_input("Enter password", type='password', placeholder="Enter password")
    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    teacher_pass_confirm = st.text_input("Confirm your password", type='password', placeholder="Confirm password")
    st.markdown("<br>", unsafe_allow_html=True)

    btnc1, btnc2 = st.columns(2)
    with btnc1:
        if st.button('Register Now', icon=':material/passkey:', use_container_width=True):  # fix 4
            success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
            if success:
                st.success(message)
                time.sleep(1)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)
    with btnc2:
        if st.button('Login Instead', type="primary", icon=':material/login:', use_container_width=True):  # fix 4
            st.session_state.teacher_login_type = 'login'
            st.rerun()