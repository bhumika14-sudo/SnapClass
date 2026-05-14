import streamlit as st
from PIL import Image

@st.dialog("Capture or Upload photos")
def add_photos_dialog():
    if "attendance_images" not in st.session_state:
        st.session_state["attendance_images"] = []

    if "photo_tab" not in st.session_state:
        st.session_state["photo_tab"] = "camera"

    if "last_camera_photo" not in st.session_state:
        st.session_state["last_camera_photo"] = None
    st.write("Add classroom photos to scan for attendance")

    t1, t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state["photo_tab"] == "camera" else "tertiary"
        if st.button("Camera", type=type_camera, width='stretch'):
            st.session_state["photo_tab"] = "camera"
            st.rerun()
    with t2:
        type_upload = "primary" if st.session_state["photo_tab"] == "upload" else "tertiary"
        if st.button("Upload photos", type=type_upload, width='stretch'):
            st.session_state["photo_tab"] = "upload"
            st.rerun()

    if st.session_state["photo_tab"] == "camera":
        cam_photo = st.camera_input("Take Snapshot", key="dialog_cam")
        if cam_photo:
            if cam_photo.name != st.session_state["last_camera_photo"]:
                captured_img = Image.open(cam_photo)
                st.session_state["attendance_images"].append(captured_img)
                st.session_state["last_camera_photo"] = cam_photo.name
                st.toast("Photo Captured Successfully")

    if st.session_state["photo_tab"] == "upload":
        uploaded_files = st.file_uploader(
            "Choose image files",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="dialog_upload"
        )

        if uploaded_files:
            st.session_state["attendance_images"] = [Image.open(f) for f in uploaded_files]
            st.toast("Photos Uploaded Successfully")
    if st.session_state.get("attendance_images", []):

        st.divider()
        st.subheader("Selected Photos")

        cols = st.columns(3)
        for idx, img in enumerate(st.session_state["attendance_images"]):
            with cols[idx % 3]:
                st.image(img, use_container_width=True, caption=f"Photo {idx + 1}")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Clear All Photos", type="tertiary", width='stretch', icon=":material/delete:"):
            st.session_state["attendance_images"] = []
            if "dialog_upload" in st.session_state:
                del st.session_state["dialog_upload"]
            if "dialog_cam" in st.session_state:
                del st.session_state["dialog_cam"]
            st.session_state["last_camera_photo"] = None
            st.toast("All photos cleared")
            st.rerun()
    with c2:
        if st.button("Done", type="primary", width='stretch'):
            st.rerun()