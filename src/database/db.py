from src.database.config import supabase
import bcrypt

def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())

def check_teacher_exists(username):
    response = supabase.table('teachers').select('username').eq('username', username).execute()
    return len(response.data) > 0

def create_teacher(username, password, name):
    data = {"username": username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data

def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None

def get_all_students():
    response = supabase.table('students').select("*").execute()
    return response.data

def create_student(new_name, face_embedding=None, voice_embedding=None, roll_no=None, section=None):
    data = {
        'name': new_name,
        'face_embedding': face_embedding,
        'voice_embedding': voice_embedding,
        'roll_no': roll_no,
        'section': section
    }
    response = supabase.table('students').insert(data).execute()
    return response.data

def create_subject(subject_code, name, section, teacher_id):
    existing = supabase.table("subjects")\
        .select("*")\
        .eq("subject_code", subject_code)\
        .eq("teacher_id", teacher_id)\
        .execute()
    if existing.data:
        return None, "Subject with this code already exists!"
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data, None

def get_teacher_subject(teacher_id):
    response = supabase.table('subjects')\
        .select("*, subject_students(count), attendance_logs(timestamp)")\
        .eq("teacher_id", teacher_id)\
        .execute()
    subjects = response.data

    for sub in subjects:
        sub['total_students'] = sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        attendance = sub.get('attendance_logs', [])
        unique_sessions = len(set(log['timestamp'] for log in attendance))
        sub['total_classes'] = unique_sessions
        sub.pop('subject_students', None)
        sub.pop('attendance_logs', None)

    return subjects

def enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, "subject_id": subject_id}
    response = supabase.table('subject_students').insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id, subject_id):
    response = supabase.table('subject_students').delete()\
        .eq('student_id', student_id)\
        .eq('subject_id', subject_id)\
        .execute()
    return response.data

def get_student_subjects(student_id):
    response = supabase.table('subject_students')\
        .select('*, subjects(*)')\
        .eq('student_id', student_id)\
        .execute()
    return response.data

def get_student_attendance(student_id):
    response = supabase.table('attendance_logs')\
        .select('*, subjects(*)')\
        .eq('student_id', student_id)\
        .eq('is_present', True)\
        .execute()
    return response.data

def create_attendance(logs):
    # fix: validate student_id exists before inserting to avoid foreign key crash
    valid_logs = []
    for log in logs:
        check = supabase.table('students')\
            .select('student_id')\
            .eq('student_id', log['student_id'])\
            .execute()
        if check.data:
            valid_logs.append(log)

    if not valid_logs:
        raise Exception(
            "No valid students found in DB — please re-enroll students and retrain the face model."
        )

    response = supabase.table('attendance_logs').insert(valid_logs).execute()
    return response.data

def get_student_by_face_label(face_label):
    response = supabase.table('students').select("*").eq('student_id', face_label).execute()
    return response.data[0] if response.data else None

def get_attendance_for_teacher(teacher_id):
    subjects_res = supabase.table('subjects')\
        .select('subject_id')\
        .eq('teacher_id', teacher_id)\
        .execute()

    if not subjects_res.data:
        return []

    subject_ids = [s['subject_id'] for s in subjects_res.data]

    response = supabase.table('attendance_logs')\
        .select('*, subjects(*)')\
        .in_('subject_id', subject_ids)\
        .execute()

    return response.data