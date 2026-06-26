# Frontend/app.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
# ✅ Fixed import — was "from Frontend.components.styles" which crashes
#    because when running from project root, Frontend/ is already the cwd context
from components.styles import inject_styles

st.set_page_config(
    page_title="FinSight — Personal Finance Coach",
    page_icon="📊",
    layout="wide"
)
inject_styles()

st.markdown('<div class="hero-title">Your Bank-Statement Knows More<br>About You Than You Think.</div>',
            unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Upload your statement. Get a personal finance diagnosis in seconds.<br>'
            'Not generic tips — advice built from your actual transactions.</div>',
            unsafe_allow_html=True)

st.write("")
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("Analyze My Statement →", type="primary", use_container_width=True):
        st.switch_page("pages/1_Upload.py")

st.divider()

st.subheader("How it works")
c1, c2, c3 = st.columns(3)
steps = [
    ("1", "Upload",  "CSV or PDF bank statement — system reads every transaction"),
    ("2", "Analyze", "5 AI agents find patterns, score your finances, build your action plan"),
    ("3", "Act",     "Get specific steps, savings opportunities, and scheme recommendations"),
]
for col, (num, title, desc) in zip([c1, c2, c3], steps):
    with col:
        st.markdown(f"""
        <div class="step-box">
          <div class="step-num">{num}</div>
          <b>{title}</b><br>
          <span style="color:#64748B;font-size:14px">{desc}</span>
        </div>""", unsafe_allow_html=True)

st.divider()
st.subheader("What you get")
f1, f2, f3, f4 = st.columns(4)
features = [
    ("📊", "Spending Breakdown",  "Category-wise breakdown of every rupee"),
    ("🧠", "Behavioral Patterns", "Impulse spend, weekend habits, subscriptions"),
    ("💡", "Personalized Plan",   "3–5 specific actions based on your data"),
    ("🏦", "Scheme Matching",     "SIPs, PPF, govt schemes you qualify for"),
]
for col, (icon, title, desc) in zip([f1, f2, f3, f4], features):
    with col:
        st.markdown(f"""
        <div class="step-box">
          <div style="font-size:28px">{icon}</div>
          <b style="font-size:14px">{title}</b><br>
          <span style="color:#64748B;font-size:13px">{desc}</span>
        </div>""", unsafe_allow_html=True)