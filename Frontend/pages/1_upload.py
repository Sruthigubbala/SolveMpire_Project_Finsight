import streamlit as st
import pandas as pd

st.set_page_config(page_title="Upload | FinSight", layout="wide")

st.title("Upload Your Bank Statement")
st.caption("Supported formats: CSV, PDF  ·  Your data is never stored permanently")

# ── Helper: build mock result from sample data ──────────────────────────────
def build_mock_result():
    data = {
        "date":        ["2024-05-01","2024-05-02","2024-05-03","2024-05-04",
                        "2024-05-05","2024-05-06","2024-05-07","2024-05-08",
                        "2024-05-09","2024-05-10","2024-05-11","2024-05-12",
                        "2024-05-13","2024-05-14","2024-05-15"],
        "description": ["Zomato Order","Uber Ride","Salary Credit","Netflix Subscription",
                        "Amazon Purchase","Petrol Fill","Swiggy Order","Electricity Bill",
                        "Zomato Order","Spotify","Swiggy Order","Amazon Prime",
                        "Uber Ride","Medplus Pharmacy","Zomato Order"],
        "amount":      [320,180,25000,649,1200,800,550,1100,420,119,380,299,220,340,310],
        "type":        ["Debit","Debit","Credit","Debit","Debit","Debit","Debit","Debit",
                        "Debit","Debit","Debit","Debit","Debit","Debit","Debit"],
        "category":    ["food","transport","income","subscriptions","shopping","transport",
                        "food","utilities","food","subscriptions","food","subscriptions",
                        "transport","medical","food"],
        "weekday":     ["Wednesday","Thursday","Friday","Saturday","Sunday","Monday",
                        "Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday",
                        "Monday","Tuesday","Wednesday"],
        "month":       ["2024-05"] * 15,
    }
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])

    debits = df[df["type"] == "Debit"]
    by_cat = debits.groupby("category")["amount"].sum().sort_values(ascending=False)
    weekend = debits[debits["weekday"].isin(["Saturday","Sunday"])]["amount"].sum()
    subs = debits[debits["category"] == "subscriptions"]
    sub_detail = subs.groupby("description")["amount"].sum().to_dict()

    patterns = {
        "total_spent":         round(debits["amount"].sum(), 2),
        "by_category":         {k: round(v,2) for k,v in by_cat.items()},
        "weekend_spend":       round(weekend, 2),
        "subscription_total":  round(subs["amount"].sum(), 2),
        "subscription_detail": sub_detail,
        "top_category":        by_cat.index[0],
        "transaction_count":   len(debits),
    }

    savings = [
        {"title": "Reduce large food orders",     "detail": "4 food orders above ₹300 detected",
         "saving": 480,  "tip": "Set a ₹300 cap per food order"},
        {"title": "Cancel one subscription",      "detail": "You pay ₹1,067/month on subscriptions",
         "saving": 119,  "tip": "Audit which services you used this month"},
        {"title": "Control weekend spending",     "detail": "Weekend spend ₹929 — higher than weekday average",
         "saving": 250,  "tip": "Plan weekend activities with a fixed budget"},
    ]

    health = {
        "score": 62, "label": "Moderate",
        "breakdown": [
            {"label": "Savings rate: 24.2%",                   "good": True},
            {"label": "Subscriptions: ₹1,067/month",           "good": False},
            {"label": "Weekend spending: 15% of total",        "good": True},
            {"label": "Top category (food): 38% of spend",     "good": None},
            {"label": "3 savings opportunities missed",        "good": False},
        ]
    }

    advice = (
        "1. You spent ₹1,580 on food this month — set a daily food budget of ₹200 (₹6,000/month cap).\n"
        "2. Cancel Spotify (₹119/month) — you have Netflix + Amazon Prime + Hotstar already.\n"
        "3. Your weekend spend (₹929) spikes on Saturdays — plan meals at home on weekends.\n"
        "4. Set up a ₹500/month recurring RD — your salary credit shows you can afford it.\n"
        "5. Amazon purchases (₹1,200) — use a 24-hour cart rule before buying anything above ₹500."
    )

    schemes = (
        "Based on your income of ₹25,000/month and spending pattern:\n\n"
        "1. **RD (Recurring Deposit)** — Start with ₹500/month at SBI or Post Office. Returns 6.8% p.a. No lock-in risk.\n"
        "2. **ELSS Mutual Fund SIP** — ₹500/month via Groww or Zerodha Coin. Historical ~12% returns. Saves tax under 80C.\n"
        "3. **PPF (Public Provident Fund)** — ₹500/year minimum. 7.1% tax-free returns. Best for long-term wealth."
    )

    return {"df": df, "patterns": patterns, "savings_opportunities": savings,
            "health_score": health, "advice": advice, "schemes": schemes}


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Upload File", "Try with Sample Data"])

with tab1:
    uploaded = st.file_uploader(
        "Drag and drop your bank statement",
        type=["csv", "pdf"],
        label_visibility="collapsed"
    )
    with st.expander("What format should my CSV be?"):
        st.code("""Date,Description,Amount,Type
01-05-2024,Zomato Order,320,Debit
02-05-2024,Salary Credit,25000,Credit
03-05-2024,Netflix,649,Debit""")

    if uploaded:
        st.success(f"✓ {uploaded.name} ready")
        st.info("⚠️ Backend agents not connected yet. Use 'Try with Sample Data' to see the full dashboard.")

with tab2:
    st.info("No file needed — click below to load a sample bank statement and see the full dashboard.")
    st.markdown("""
    **Sample data includes:**
    - 15 transactions across food, transport, subscriptions, shopping
    - ₹25,000 salary credit
    - Zomato, Swiggy, Netflix, Spotify, Uber, Amazon
    """)
    if st.button("▶ Run Demo Analysis", type="primary"):
        with st.spinner("Building analysis from sample data..."):
            st.session_state["result"] = build_mock_result()
        st.success("✅ Done! Redirecting to Dashboard...")
        st.switch_page("pages/2_Dashboard.py")