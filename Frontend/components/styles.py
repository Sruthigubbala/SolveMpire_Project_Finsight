## frontend/components/styles.py
import streamlit as st

def inject_styles():
    st.markdown("""
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
        color: #0F172A;
    }

    .hero-title {
        font-size: 46px;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
        letter-spacing: -1px;
    }

    .hero-sub {
        font-size: 18px;
        color: #64748B;
        margin-top: 12px;
        margin-bottom: 20px;
    }

    .step-box {
        background: linear-gradient(135deg, #FFFFFF, #F8FAFC);
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    .step-num {
        font-size: 32px;
        font-weight: 700;
        color: #2563EB;
    }

    .advice-box {
        background: #EFF6FF;
        border-left: 4px solid #2563EB;
        padding: 22px;
        border-radius: 0 12px 12px 0;
        font-size: 15px;
        line-height: 1.8;
        box-shadow: 0 2px 8px rgba(37,99,235,0.08);
    }

    .answer-box {
        background: #ECFDF5;
        border-left: 4px solid #10B981;
        padding: 22px;
        border-radius: 0 12px 12px 0;
        margin-top: 16px;
        font-size: 15px;
        line-height: 1.8;
        box-shadow: 0 2px 8px rgba(16,185,129,0.08);
    }

    .stButton > button {
        background: linear-gradient(90deg, #2563EB, #1D4ED8);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: 600;
    }

    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #E5E7EB;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    }

    </style>
    """, unsafe_allow_html=True)