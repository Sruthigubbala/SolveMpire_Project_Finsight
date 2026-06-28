# Frontend/app.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from components.styles import inject_styles

st.set_page_config(
    page_title="FinSight — Personal Finance Coach",
    page_icon="📊",
    layout="wide"
)
inject_styles()

# ── Hero ─────────────────────────────────────────────────────
st.markdown('<div class="hero-eyebrow">AI-Powered Financial Analysis</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-title">Your Bank Statement Knows More<br>'
    'About You Than <span class="accent">You Think.</span></div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="hero-sub">Upload your statement. Get a personal finance diagnosis in seconds.'
    '<br>Not generic tips — advice built from your actual transactions.</div>',
    unsafe_allow_html=True
)

st.write("")
col1, col2, col3 = st.columns([1.2, 0.9, 4])
with col1:
    if st.button ("🚀Analyze My Statement", type="primary", use_container_width=True):
        st.switch_page("pages/1_upload.py")

st.divider()

# ── How it works ──────────────────────────────────────────────
st.markdown('<div class="section-header"><h2>How it works</h2></div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
steps = [
    ("01", "Upload",  "Drop your CSV or PDF bank statement — every transaction is read and categorized automatically."),
    ("02", "Analyze", "5 specialised AI agents find patterns, score your finances, and build your action plan."),
    ("03", "Act",     "Receive specific steps, savings opportunities, and government scheme recommendations."),
]
for col, (num, title, desc) in zip([c1, c2, c3], steps):
    with col:
        st.markdown(f"""
        <div class="step-box">
          <div class="step-num">{num}</div>
          <b>{title}</b>
          <span class="desc">{desc}</span>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── What you get ──────────────────────────────────────────────
st.markdown('<div class="section-header"><h2>What you get</h2></div>', unsafe_allow_html=True)

f1, f2, f3, f4 = st.columns(4)
features = [
    ("📊", "Spending Breakdown",  "Category-wise breakdown of every rupee spent across your statement."),
    ("🧠", "Behavioral Patterns", "Impulse spend, weekend habits, and hidden subscriptions flagged instantly."),
    ("💡", "Personalized Plan",   "3–5 specific actions based on your actual numbers, not generic advice."),
    ("🏦", "Scheme Matching",     "SIPs, PPF, and government schemes matched to your income profile."),
]
for col, (icon, title, desc) in zip([f1, f2, f3, f4], features):
    with col:
        st.markdown(f"""
        <div class="step-box">
          <div style="font-size:34px;margin-bottom:14px">{icon}</div>
          <b style="font-size:14px">{title}</b>
          <span class="desc">{desc}</span>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Trust bar ─────────────────────────────────────────────────
st.markdown('<div class="section-header"><h2>Why FinSight?</h2></div>', unsafe_allow_html=True)

t1, t2, t3 = st.columns(3)
trust_items = [
    ("🔒", "Privacy First",     "Your data is processed in-memory and never stored or shared."),
    ("⚡", "Instant Results",   "Full analysis completes in under 30 seconds using 5 AI agents."),
    ("🎯", "Indian-Specific",   "Recommendations calibrated for Indian financial products and schemes."),
]
for col, (icon, title, desc) in zip([t1, t2, t3], trust_items):
    with col:
        st.markdown(f"""
        <div class="step-box" style="text-align:center">
          <div style="font-size:28px;margin-bottom:10px">{icon}</div>
          <strong style="font-size:14px;color:#1E293B">{title}</strong>
          <p style="font-size:13px;color:#64748B;margin-top:6px;margin-bottom:0">{desc}</p>
        </div>""", unsafe_allow_html=True)
    