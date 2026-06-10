## frontend/components/styles.py
import streamlit as st

def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .hero-title { font-size: 42px; font-weight: 700; color: #0A1628; line-height: 1.2; }
    .hero-sub   { font-size: 17px; color: #64748B; margin-top: 12px; }
    .step-box   { background: #F8FAFC; border: 1px solid #E2E8F0;
                  border-radius: 10px; padding: 20px; text-align: center; }
    .step-num   { font-size: 28px; font-weight: 700; color: #1E5EFF; }
    .advice-box { background:#EFF6FF; border-left:3px solid #1E5EFF;
                  padding:20px; border-radius:0 8px 8px 0; font-size:15px; line-height:1.8; }
    .answer-box { background:#F0FDF4; border-left:3px solid #00A86B;
                  padding:20px; border-radius:0 8px 8px 0; margin-top:16px; }
    </style>
    """, unsafe_allow_html=True)