import streamlit as st

def style_background_home():
    st.markdown("""
        <style>
            .stApp {
                background: #5865F2 !important;
            }

            .stApp div[data-testid="stColumn"] {
                background-color: #E0E3FF !important;
                padding: 2.5rem !important;
                border-radius: 5rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

def style_background_dashboard():
    st.markdown("""
        <style>
            .stApp {
                background: #C9CBF0 !important;
            }
        </style>
    """, unsafe_allow_html=True)


def style_base_layout():
    st.markdown("""
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Cabin+Condensed:wght@400;500;600;700&family=Outfit:wght@100..900&display=swap');

        /* Hide Streamlit Header */
        #MainMenu, footer, header {
            visibility: hidden;
        }

        .block-container {
            padding-top: 1.5rem !important;
        }

        /* MAIN HEADINGS */
        h1 {
            font-family: 'Cabin Condensed', sans-serif !important;
            font-size: 3.5rem !important;
            line-height: 1.1 !important;
            margin-bottom: 0rem !important;
            color: white !important;
            font-weight: 700 !important;
        }

        h2 {
            font-family: 'Cabin Condensed', sans-serif !important;
            font-size: 3.5rem !important;
            line-height: 0.9 !important;
            margin-bottom: 0rem !important;
            color: #22243B !important;
            font-weight: 700 !important;
        }

        /* NORMAL TEXT */
        h3, h4, p {
            font-family: 'Outfit', sans-serif !important;
            color: white !important;
        }

        /* BUTTONS */
        button {
            border-radius: 1.5rem !important;
            background-color: #5865F2 !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: transform 0.25s ease-in-out !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
        }

        button[kind="secondary"] {
            border-radius: 1.5rem !important;
            background-color: #EB459E !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: transform 0.25s ease-in-out !important;
        }

        button[kind="tertiary"] {
            border-radius: 1.5rem !important;
            background-color: black !important;
            color: white !important;
            padding: 10px 20px !important;
            border: none !important;
            transition: transform 0.25s ease-in-out !important;
        }

        button:hover {
            transform: scale(1.05);
        }

        /* ── DIALOG / POPUP FIX (works on both light & dark theme) ── */

        /* Dialog background always white */
        div[data-testid="stDialog"] > div > div {
            background-color: #ffffff !important;
            border-radius: 1.5rem !important;
            padding: 1.5rem !important;
        }

        /* All text inside dialog always black */
        div[data-testid="stDialog"] h1,
        div[data-testid="stDialog"] h2,
        div[data-testid="stDialog"] h3,
        div[data-testid="stDialog"] h4,
        div[data-testid="stDialog"] p,
        div[data-testid="stDialog"] label,
        div[data-testid="stDialog"] span,
        div[data-testid="stDialog"] div {
            color: #111111 !important;
        }

        /* Input fields inside dialog */
        div[data-testid="stDialog"] input,
        div[data-testid="stDialog"] textarea,
        div[data-testid="stDialog"] select {
            background-color: #f5f5f5 !important;
            color: #111111 !important;
            border: 1px solid #dddddd !important;
            border-radius: 0.5rem !important;
        }

        /* Input label inside dialog */
        div[data-testid="stDialog"] .stTextInput label,
        div[data-testid="stDialog"] .stSelectbox label {
            color: #111111 !important;
            font-weight: 600 !important;
        }

        /* Warning / success / error boxes inside dialog */
        div[data-testid="stDialog"] .stAlert {
            background-color: #f0f0f0 !important;
            color: #111111 !important;
        }

        </style>
    """, unsafe_allow_html=True)