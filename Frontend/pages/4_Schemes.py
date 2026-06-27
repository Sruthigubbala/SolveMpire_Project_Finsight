# Frontend/pages/4_Schemes.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from components.styles import inject_styles

st.set_page_config(page_title="Schemes | FinSight", page_icon="🏦", layout="wide")
inject_styles()

# ── Guard ─────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.markdown('<div class="warning-box"><strong>No analysis found.</strong> Please upload a statement first.</div>',
                unsafe_allow_html=True)
    st.write("")
    if st.button("← Go to Upload", type="primary"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

result   = st.session_state["result"]
patterns = result["patterns"]
schemes_text = result.get("schemes", "")

# ── Header ────────────────────────────────────────────────────
st.markdown('<div class="section-header"><h1>Savings Schemes for You</h1></div>', unsafe_allow_html=True)
st.caption("Matched to your income profile and spending patterns by the AI agent")

st.write("")

# ── Profile snapshot ──────────────────────────────────────────
total_spent = patterns["total_spent"]
invest_budget = total_spent * 0.15

p1, p2, p3 = st.columns(3)
with p1: st.metric("Monthly Spend",        f"₹{total_spent:,.0f}")
with p2: st.metric("Investment Budget",    f"₹{invest_budget:,.0f}", delta="~15% of spend")
with p3: st.metric("Subscription Savings", f"₹{patterns['subscription_total']:,.0f}", delta="potential to redirect")

st.divider()

# ── AI Recommendation ─────────────────────────────────────────────────────────
st.subheader("🤖 AI Recommendation")

schemes_data = result.get("schemes", "")
schemes_text = ""

# ── Robust Clean Parsing to Drop Metadata Wrappers ────────────────────────────
if isinstance(schemes_data, list):
    # If it's a list, check if elements are dicts with a 'text' key
    extracted_texts = []
    for item in schemes_data:
        if isinstance(item, dict) and "text" in item:
            extracted_texts.append(item["text"])
        else:
            extracted_texts.append(str(item))
    schemes_text = "\n".join(extracted_texts)

elif isinstance(schemes_data, dict):
    schemes_text = schemes_data.get("text", str(schemes_data))

else:
    # If it is a messy string representing raw API output structure
    schemes_data_str = str(schemes_data).strip()
    
    # Try converting structural string literal safely into an object
    if schemes_data_str.startswith("[") or schemes_data_str.startswith("{"):
        try:
            parsed = ast.literal_eval(schemes_data_str)
            if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                schemes_text = parsed[0].get("text", schemes_data_str)
            elif isinstance(parsed, dict):
                schemes_text = parsed.get("text", schemes_data_str)
            else:
                schemes_text = schemes_data_str
        except Exception:
            # Fallback regex strip if literal compilation fails
            # This directly eliminates patterns matching: [{'type': 'text', 'text': '
            cleaned = re.sub(r"^\[?\s*\{\s*['\"]type['\"]:\s*['\"]text['\"],\s*['\"]text['\"]:\s*['\"]", "", schemes_data_str)
            # Remove trailing brackets/braces from the end of string
            cleaned = re.sub(r"['\"]\}\s*\]?$", "", cleaned)
            schemes_text = cleaned
    else:
        schemes_text = schemes_data_str

# Unescape literal raw slash-n characters back into proper layout breaks
schemes_text = schemes_text.replace("\\n", "\n")

# Render beautifully matching your layout
with st.container(border=True):
    st.markdown(schemes_text)

st.divider()

# ── Static scheme reference cards ─────────────────────────────
st.markdown('<div class="section-header"><h2>Popular Indian Savings Schemes</h2></div>', unsafe_allow_html=True)
st.caption("Quick reference — eligibility and returns for common instruments")

schemes_ref = [
    {
        "name":        "Public Provident Fund (PPF)",
        "badge":       "Government",
        "badge_class": "badge-gov",
        "return":      "7.1% p.a.",
        "min":         "₹500/year",
        "max":         "₹1.5 lakh/year",
        "lock":        "15 years",
        "tax":         "EEE — fully tax-free",
        "good_for":    "Long-term wealth building with guaranteed returns",
        "icon":        "🏛️",
    },
    {
        "name":        "Systematic Investment Plan (SIP)",
        "badge":       "Mutual Fund",
        "badge_class": "badge-mf",
        "return":      "10–14% p.a. (equity, hist.)",
        "min":         "₹500/month",
        "max":         "No limit",
        "lock":        "ELSS: 3 yrs · Others: none",
        "tax":         "ELSS qualifies u/s 80C",
        "good_for":    "Wealth creation through rupee-cost averaging",
        "icon":        "📈",
    },
    {
        "name":        "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "badge":       "Government",
        "badge_class": "badge-gov",
        "return":      "4% p.a. savings",
        "min":         "Zero balance",
        "max":         "No limit",
        "lock":        "None",
        "tax":         "Standard savings account tax rules",
        "good_for":    "Basic banking + ₹2 lakh accident insurance",
        "icon":        "🏦",
    },
    {
        "name":        "Recurring Deposit (RD)",
        "badge":       "Bank",
        "badge_class": "badge-bank",
        "return":      "5.5–7% p.a.",
        "min":         "₹100/month",
        "max":         "No limit",
        "lock":        "6 months – 10 years",
        "tax":         "Interest taxable per slab",
        "good_for":    "Disciplined monthly saving with guaranteed returns",
        "icon":        "💰",
    },
    {
        "name":        "National Pension System (NPS)",
        "badge":       "Government",
        "badge_class": "badge-gov",
        "return":      "8–12% p.a. (market-linked)",
        "min":         "₹500/contribution",
        "max":         "No upper limit",
        "lock":        "Till age 60",
        "tax":         "Additional ₹50k u/s 80CCD(1B)",
        "good_for":    "Retirement corpus with extra tax benefit",
        "icon":        "🌅",
    },
    {
        "name":        "Sukanya Samriddhi Yojana (SSY)",
        "badge":       "Government",
        "badge_class": "badge-gov",
        "return":      "8.2% p.a.",
        "min":         "₹250/year",
        "max":         "₹1.5 lakh/year",
        "lock":        "21 years / girl turns 18",
        "tax":         "EEE — fully tax-free",
        "good_for":    "Parents of daughters — girl child savings",
        "icon":        "👧",
    },
]

col1, col2 = st.columns(2)
for i, s in enumerate(schemes_ref):
    with (col1 if i % 2 == 0 else col2):
        st.markdown(f"""
        <div class="scheme-card">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
            <span style="font-size:28px">{s['icon']}</span>
            <div>
              <div style="font-weight:700;font-size:16px;color:#1E293B">{s['name']}</div>
              <span class="scheme-badge {s['badge_class']}">{s['badge']}</span>
            </div>
          </div>
          <table style="width:100%;border-collapse:collapse;font-size:13px">
            <tr><td style="color:#94A3B8;padding:4px 0;width:45%">Expected return</td><td style="font-weight:600;color:#1E293B">{s['return']}</td></tr>
            <tr><td style="color:#94A3B8;padding:4px 0">Minimum invest.</td><td style="font-weight:600;color:#1E293B">{s['min']}</td></tr>
            <tr><td style="color:#94A3B8;padding:4px 0">Maximum invest.</td><td style="font-weight:600;color:#1E293B">{s['max']}</td></tr>
            <tr><td style="color:#94A3B8;padding:4px 0">Lock-in period</td><td style="font-weight:600;color:#1E293B">{s['lock']}</td></tr>
            <tr><td style="color:#94A3B8;padding:4px 0">Tax benefit</td><td style="font-weight:600;color:#1E293B">{s['tax']}</td></tr>
          </table>
          <div style="margin-top:14px;padding:10px 14px;background:#F8FAFC;border-radius:8px;font-size:13px;color:#374151">
            💡 <em>{s['good_for']}</em>
          </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Disclaimer ────────────────────────────────────────────────
st.markdown("""
<div class="info-box" style="font-size:13px;color:#64748B">
  <strong>Disclaimer:</strong> The scheme information above is for educational purposes only.
  Returns shown are historical or indicative. Please consult a SEBI-registered financial advisor
  before making investment decisions. Interest rates are subject to government revision.
</div>""", unsafe_allow_html=True)

st.divider()
nav1, nav2 = st.columns(2)
with nav1:
    if st.button("← Back to Dashboard"):
        st.switch_page("pages/2_Dashboard.py")
with nav2:
    if st.button("💬  Ask More Questions →"):
        st.switch_page("pages/3_Ask_Questions.py")