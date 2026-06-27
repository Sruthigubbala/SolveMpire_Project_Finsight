# Frontend/pages/about.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from components.styles import inject_styles

st.set_page_config(page_title="About | FinSight", page_icon="ℹ️", layout="wide")
inject_styles()

# ── Hero ──────────────────────────────────────────────────────
st.markdown('<div class="hero-eyebrow">About FinSight</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title" style="font-size:40px"><span class="accent">FINSIGHT</span></div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub" style="font-size:16px">A five-agent AI system that turns raw bank statements'
    ' into actionable financial coaching — built at the intersection of AI and personal finance.</div>',
    unsafe_allow_html=True
)

st.divider()

# ── Stats ─────────────────────────────────────────────────────
st.markdown('<div class="section-header"><h2>By the numbers</h2></div>', unsafe_allow_html=True)

s1, s2, s3, s4 = st.columns(4)
stats = [
    ("5",    "AI Agents"),
    ("4",    "Knowledge Docs"),
    ("100%", "Privacy First"),
    ("< 30s","Analysis Time"),
]
for col, (val, lbl) in zip([s1, s2, s3, s4], stats):
    with col:
        st.markdown(f"""
        <div class="about-stat">
          <div class="stat-val">{val}</div>
          <div class="stat-label">{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── How it works (technical) ──────────────────────────────────
st.markdown('<div class="section-header"><h2>The 5-Agent Pipeline</h2></div>', unsafe_allow_html=True)

agents = [
    ("01", "Statement Parser",   "🗂️",
     "Reads CSV and PDF bank statements, cleans transaction data, and categorises every entry using rule-based matching and fuzzy logic."),
    ("02", "Pattern Analyser",   "🔍",
     "Finds spending patterns: weekend vs weekday split, subscription detection, merchant concentration, and monthly trends."),
    ("03", "Calculators",        "🧮",
     "Computes the Budget Health Score across 5 dimensions and identifies concrete savings opportunities with specific rupee amounts."),
    ("04", "Advice Agent",       "💡",
     "Uses RAG over RBI financial literacy documents to generate a structured, data-grounded action plan — not generic tips."),
    ("05", "Product Matcher",    "🏦",
     "Matches the user's investment budget and risk profile to government schemes and financial products from the AMFI/PMJDY corpus."),
]

for num, name, icon, desc in agents:
    st.markdown(f"""
    <div class="scheme-card" style="display:flex;align-items:flex-start;gap:18px;margin-bottom:12px">
      <div style="min-width:48px;height:48px;background:linear-gradient(135deg,#EEF3FF,#F0FDFA);
                  border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px">{icon}</div>
      <div>
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
          <span style="font-family:'DM Mono',monospace;font-size:11px;font-weight:600;color:#1E5EFF">{num}</span>
          <span style="font-weight:700;font-size:15px;color:#1E293B">{name}</span>
        </div>
        <p style="font-size:14px;color:#64748B;margin:0;line-height:1.65">{desc}</p>
      </div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Tech Stack ────────────────────────────────────────────────
st.markdown('<div class="section-header"><h2>Tech Stack</h2></div>', unsafe_allow_html=True)

tech_cols = st.columns(3)
tech_categories = [
    ("🤖  AI & Language Models", [
        ("#EEF3FF", "#1E5EFF", "Google Gemini 3.1"),
        ("#EEF3FF", "#1E5EFF", "LangChain"),
        ("#EEF3FF", "#1E5EFF", "RAG Pipeline"),
    ]),
    ("📚  Knowledge & Search", [
        ("#ECFDF5", "#00A86B", "FAISS Vector Store"),
        ("#ECFDF5", "#00A86B", "HuggingFace Embeddings"),
        ("#ECFDF5", "#00A86B", "PyMuPDF / pdfplumber"),
    ]),
    ("🖥️  Frontend & Data", [
        ("#FFF7ED", "#EA580C", "Streamlit"),
        ("#FFF7ED", "#EA580C", "Plotly"),
        ("#FFF7ED", "#EA580C", "Pandas"),
    ]),
]

for col, (category, pills) in zip(tech_cols, tech_categories):
    with col:
        st.markdown(f"<p style='font-weight:700;font-size:14px;color:#1E293B;margin-bottom:10px'>{category}</p>",
                    unsafe_allow_html=True)
        pills_html = "".join(
            f'<span style="display:inline-block;background:{bg};color:{fg};font-size:12px;'
            f'font-weight:600;padding:5px 14px;border-radius:100px;margin:4px 4px 4px 0">{name}</span>'
            for bg, fg, name in pills
        )
        st.markdown(pills_html, unsafe_allow_html=True)

st.divider()

# ── Knowledge base ────────────────────────────────────────────
st.markdown('<div class="section-header"><h2>Knowledge Base</h2></div>', unsafe_allow_html=True)
st.caption("The RAG system grounds advice in authoritative Indian financial documents")

docs = [
    ("📘", "AMFI Mutual Fund Basics",        "Association of Mutual Funds in India — investor education guide"),
    ("📗", "RBI Financial Literacy",         "Reserve Bank of India — personal finance and banking literacy"),
    ("📙", "PPF Scheme Document",            "Public Provident Fund — official scheme rules and guidelines"),
    ("📕", "PMJDY Scheme Document",          "Pradhan Mantri Jan Dhan Yojana — financial inclusion scheme"),
]

d1, d2 = st.columns(2)
for i, (icon, title, desc) in enumerate(docs):
    with (d1 if i % 2 == 0 else d2):
        st.markdown(f"""
        <div class="info-box" style="margin-bottom:12px;display:flex;gap:14px;align-items:flex-start">
          <span style="font-size:26px">{icon}</span>
          <div>
            <strong style="font-size:14px;color:#1E293B">{title}</strong>
            <p style="font-size:13px;color:#64748B;margin:4px 0 0">{desc}</p>
          </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Mission ───────────────────────────────────────────────────
st.markdown("""
<div class="advice-box">
  <strong style="font-size:16px">Our Mission</strong><br><br>
  Most Indians receive no financial coaching. Banks send statements without context.
  Generic tips don't account for individual spending. FinSight bridges this gap —
  reading your actual numbers and producing advice that's grounded in your reality,
  not a template.
  <br><br>
  <em>Built  by Team FINSIGHT.</em>
</div>""", unsafe_allow_html=True)

st.divider()
if st.button("← Back to Home"):
    st.switch_page("app.py")