import streamlit as st

st.set_page_config(page_title="Schemes | FinSight", layout="wide")

# ── Guard ─────────────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.warning("No analysis found. Please run the demo analysis first.")
    if st.button("Go to Upload"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

result = st.session_state["result"]

st.title("Savings Schemes You Qualify For")
st.caption("Matched based on your income level and spending pattern")

# ── AI Recommendation ─────────────────────────────────────────────────────────
st.subheader("AI Recommendation")
schemes_html = result["schemes"].replace("\n", "<br>")
st.markdown(f"""
<div style="background:#EFF6FF;border-left:4px solid #1E5EFF;
            padding:20px;border-radius:0 8px 8px 0;font-size:15px;line-height:2">
  {schemes_html}
</div>""", unsafe_allow_html=True)

st.divider()

# ── Scheme Cards ──────────────────────────────────────────────────────────────
st.subheader("Explore All Schemes")

SCHEMES = [
    {
        "name":    "PPF — Public Provident Fund",
        "icon":    "🏦",
        "min":     "₹500/year",
        "returns": "7.1% p.a.",
        "lock":    "15 years",
        "tax":     "Exempt (80C)",
        "best":    "Long-term wealth building — completely tax-free",
        "link":    "https://www.indiapost.gov.in",
    },
    {
        "name":    "ELSS — Equity Linked Savings Scheme (SIP)",
        "icon":    "📈",
        "min":     "₹500/month",
        "returns": "~12% historical",
        "lock":    "3 years",
        "tax":     "Deduction (80C)",
        "best":    "Medium-term growth + tax saving under 80C",
        "link":    "https://www.amfiindia.com",
    },
    {
        "name":    "RD — Recurring Deposit",
        "icon":    "🏧",
        "min":     "₹100/month",
        "returns": "6.5–7% p.a.",
        "lock":    "6 months – 10 years",
        "tax":     "Taxable",
        "best":    "Safe monthly savings habit — zero risk",
        "link":    "https://www.sbi.co.in",
    },
    {
        "name":    "NPS — National Pension System",
        "icon":    "👴",
        "min":     "₹500/month",
        "returns": "8–10% p.a.",
        "lock":    "Till retirement",
        "tax":     "Deduction (80CCD)",
        "best":    "Retirement planning — extra ₹50K deduction beyond 80C",
        "link":    "https://www.npstrust.org.in",
    },
    {
        "name":    "PM Jan Dhan Yojana",
        "icon":    "🪙",
        "min":     "₹0 (zero balance)",
        "returns": "4% savings rate",
        "lock":    "None",
        "tax":     "N/A",
        "best":    "First bank account + ₹2 lakh accident insurance free",
        "link":    "https://pmjdy.gov.in",
    },
]

for s in SCHEMES:
    with st.container():
        st.markdown(f"### {s['icon']} {s['name']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Minimum",  s["min"])
        c2.metric("Returns",  s["returns"])
        c3.metric("Lock-in",  s["lock"])
        c4.metric("Tax",      s["tax"])
        st.caption(f"✅ Best for: {s['best']}")
        st.link_button("Learn More ↗", s["link"])
        st.divider()

# ── Nav ───────────────────────────────────────────────────────────────────────
if st.button("← Back to Dashboard"):
    st.switch_page("pages/2_Dashboard.py")