import streamlit as st
def subject_card(name, code, section , stats=None, footer_callback=None):
    html = f"""
            <div style = "background:white; border-left: 8px solid #EB459E; padding:25px; border-radius: 20px; border:1px solid black; margin-bottom:20px;">
            <h5 style="margin:0; color:#1e293b; font-size:1.5rem">{name}</h5>
            <p1 style="color: #64748b; margin:10px 0;"> Code : <span style="background:#E0E3FF; color:#5865F2; padding:2px 8px;border-radius:5px;">{code} </span> | Section : {section} </p1>
            """
    if stats:
        for icon, label, value in stats:
            html += f'''
            <div style="
                background: #f8f8f8;
                border: 1px solid #eee;
                padding: 10px 20px;
                border-radius: 20px;
                font-size: 1rem;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                color: #333;
                width: fit-content;
            ">
                {icon} <span><b>{value}</b> {label}</span>
            </div>
            '''

        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
    
    if footer_callback:
        footer_callback()

