import streamlit as st
import segno 
import io

@st.dialog("Share Class Link") 
def share_subject_dialog(subject_name, subject_code):
    
    st.markdown("""
        <style>
        [data-testid="stDialog"] > div > div {
            background-color: white !important;
            color: white !important;
        }
        [data-testid="stDialog"] * {
            color: black !important;
        }
        </style>
    """, unsafe_allow_html=True)

    app_domain = "main-snapclass.streamlit.app"
    join_url = f"{app_domain}/?join-code={subject_code}"

    st.header("Scan to Join")

    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=10, border=1)
    out.seek(0)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Copy Link')
 
        st.markdown(f"""
            <div style="
                background-color: #f0f0f0;
                color: #333;
                padding: 10px 14px;
                border-radius: 8px;
                font-family: monospace;
                font-size: 0.85rem;
                margin-bottom: 10px;
                word-break: break-all;
            ">{join_url}</div>
        
            <div style="
                background-color: #f0f0f0;
                color: #333;
                padding: 10px 14px;
                border-radius: 8px;
                font-family: monospace;
                font-size: 0.85rem;
                margin-bottom: 10px;
            ">{subject_code}</div>
        """, unsafe_allow_html=True)
    
        st.info('Copy this link to share on Whatsapp or Email')

    with col2:
        st.markdown('### Scan to Join')
        st.image(
            out.getvalue(),
            use_container_width=True,
            caption='QRCODE for class joining'
        )