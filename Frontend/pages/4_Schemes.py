import streamlit as st
import ast
import re

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
    with st.container(border=True):  
        st.markdown(f"### {s['icon']} {s['name']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Minimum",  s["min"])
        c2.metric("Returns",  s["returns"])
        c3.metric("Lock-in",  s["lock"])
        c4.metric("Tax",      s["tax"])
        st.markdown(f"**💡 Best for:** {s['best']}")
        st.link_button("Learn More ↗", s["link"])

# ── Nav ───────────────────────────────────────────────────────────────────────
st.write("")  
if st.button("← Back to Dashboard", type="secondary"):
    st.switch_page("pages/2_Dashboard.py")