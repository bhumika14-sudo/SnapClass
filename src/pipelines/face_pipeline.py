import dlib
import numpy as np
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_all_students

@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, sp, facerec


def get_face_embeddings(image_np):
    # fix 2: ensure RGB and contiguous memory (PIL/Streamlit can give RGBA)
    if image_np.ndim == 3 and image_np.shape[2] == 4:
        image_np = image_np[:, :, :3]
    image_np = np.ascontiguousarray(image_np)

    detector, sp, facerec = load_dlib_models()

    # fix 1: upsample=0 instead of 1 (faster, still detects normal-size faces)
    faces = detector(image_np, 0)

    encodings = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(face_descriptor))
    return encodings


@st.cache_resource
def get_trained_model():
    X = []
    y = []

    student_db = get_all_students()

    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))

    # fix 3: return None explicitly (not 0)
    if len(X) == 0:
        return None

    # fix 4: guard SVC — needs at least 2 unique classes
    if len(set(y)) < 2:
        return None

    clf = SVC(kernel='linear', probability=True, class_weight='balanced')
    clf.fit(X, y)  # no silent except — let real errors surface

    return {'clf': clf, 'X': X, 'y': y}


def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)


def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)
    detected_student = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_student, [], len(encodings)

    clf = model_data['clf']
    X_train = model_data['X']
    y_train = model_data['y']

    all_students = sorted(list(set(y_train)))

    for encoding in encodings:
        if len(all_students) >= 2:
            predicted_id = int(clf.predict([encoding])[0])
        else:
            predicted_id = all_students[0]

        # fix 5: guard against predicted_id not in y_train
        if predicted_id not in y_train:
            continue

        idx = y_train.index(predicted_id)
        student_embedding = X_train[idx]

        best_match_score = np.linalg.norm(student_embedding - encoding)
        if best_match_score <= 0.6:
            detected_student[predicted_id] = True

    return detected_student, all_students, len(encodings)