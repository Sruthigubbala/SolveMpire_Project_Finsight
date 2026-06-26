# frontend/pages/2_Dashboard.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from Frontend.components.charts import spending_bar_chart, health_score_display
from Frontend.components.cards  import savings_opportunity_cards
from Frontend.components.styles import inject_styles

st.set_page_config(page_title="Dashboard | FinSight", layout="wide")
inject_styles()

if "result" not in st.session_state:
    st.warning("No analysis found. Please upload a statement first.")
    if st.button("Go to Upload"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

result   = st.session_state["result"]
patterns = result["patterns"]
health   = result["health_score"]
savings  = result["savings_opportunities"]

st.title("Your Financial Dashboard")
st.caption("Analyzed by 5 AI agents using your bank statement")

# ── Summary Metric Cards ─────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
metrics = [
    ("Total Spent",       f"₹{patterns['total_spent']:,.0f}",        ""),
    ("Top Category",      patterns['top_category'].title(),           ""),
    ("Health Score",      f"{health['score']}/100",                   health['label']),
    ("Savings Potential", f"₹{sum(o['saving'] for o in savings):,.0f}", "this month"),
    ("Subscriptions",     f"₹{patterns['subscription_total']:,.0f}",  "/month"),
]
for col, (label, value, sub) in zip([c1, c2, c3, c4, c5], metrics):
    with col:
        st.metric(label=label, value=value,
                  delta=sub if sub else None, delta_color="off")

st.divider()

# ── Spending Chart + Health Score ─────────────────────────────
col_left, col_right = st.columns([3, 2])
with col_left:
    st.subheader("Spending by Category")
    spending_bar_chart(patterns["by_category"])
with col_right:
    st.subheader("Budget Health Score")
    health_score_display(health)

st.divider()

# ── Savings Opportunities ─────────────────────────────────────
st.subheader("Savings Opportunities")
st.caption("Specific amounts you could have saved based on your actual transactions")
savings_opportunity_cards(savings)

st.divider()

# ── Behavioral Patterns ───────────────────────────────────────
st.subheader("Behavioral Patterns")
col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    st.metric("Weekend Spend", f"₹{patterns['weekend_spend']:,.0f}")
with col_p2:
    st.metric("Transactions", patterns['transaction_count'])
with col_p3:
    st.metric("Active Subscriptions", len(patterns['subscription_detail']))

st.divider()

# ── Action Plan ───────────────────────────────────────────────
st.subheader("Your Personalized Action Plan")
st.markdown(f'<div class="advice-box">{result["advice"].replace(chr(10),"<br>")}</div>',
            unsafe_allow_html=True)

st.divider()

# ── Subscription Audit ────────────────────────────────────────
st.subheader("Subscription Audit")
if patterns["subscription_detail"]:
    sub_data = [{"Merchant": k, "Amount (₹)": f"₹{v:,.0f}", "Frequency": "Monthly"}
                for k, v in patterns["subscription_detail"].items()]
    st.dataframe(sub_data, hide_index=True, use_container_width=True)
else:
    st.caption("No recurring subscriptions detected.")

# ── All Transactions ──────────────────────────────────────────
with st.expander("View All Transactions"):
    df = result["df"]
    st.dataframe(df[["date", "description", "amount", "category"]],
                 hide_index=True, use_container_width=True)

st.divider()
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button("Ask Questions About Your Statement →"):
        st.switch_page("pages/3_Ask_Questions.py")
with col_nav2:
    if st.button("View Savings Schemes →"):
        st.switch_page("pages/4_Schemes.py")