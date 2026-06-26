import streamlit as st

st.set_page_config(page_title="Ask Questions | FinSight", layout="wide")

# ── Guard ─────────────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.warning("No analysis found. Please run the demo analysis first.")
    if st.button("Go to Upload"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

result   = st.session_state["result"]
df       = result["df"]
patterns = result["patterns"]

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.answer-box { background:#F0FDF4; border-left:4px solid #00A86B;
              padding:20px; border-radius:0 8px 8px 0;
              font-size:15px; line-height:1.9; margin-top:16px; }
</style>
""", unsafe_allow_html=True)

st.title("Ask Questions About Your Statement")
st.caption("Ask anything in plain English — answers come from your actual transaction data")

# ── Smart local answering (no backend needed) ─────────────────────────────────
def answer_from_data(question: str) -> str:
    q = question.lower()
    by_cat   = df[df["type"]=="Debit"].groupby("category")["amount"].sum().sort_values(ascending=False)
    by_merch = df[df["type"]=="Debit"].groupby("description")["amount"].sum().sort_values(ascending=False)
    total    = by_cat.sum()
    weekend  = df[(df["type"]=="Debit") & (df["weekday"].isin(["Saturday","Sunday"]))]["amount"].sum()
    weekday_spend = df[(df["type"]=="Debit") & (~df["weekday"].isin(["Saturday","Sunday"]))]["amount"].sum()

    if any(w in q for w in ["food","zomato","swiggy","eat","restaurant"]):
        food = by_cat.get("food", 0)
        merchants = df[df["category"]=="food"].groupby("description")["amount"].sum()
        detail = ", ".join([f"{k} ₹{v:.0f}" for k,v in merchants.items()])
        return (f"You spent **₹{food:,.0f}** on food this month across {len(merchants)} merchants.\n\n"
                f"Breakdown: {detail}.\n\n"
                f"This is **{food/total*100:.1f}%** of your total spending.")

    elif any(w in q for w in ["transport","uber","ola","petrol","travel","ride"]):
        t = by_cat.get("transport", 0)
        return (f"You spent **₹{t:,.0f}** on transport this month.\n\n"
                f"This covers Uber rides and petrol fill-ups.\n\n"
                f"Tip: Carpooling or metro can reduce this by ~30%.")

    elif any(w in q for w in ["subscript","netflix","spotify","prime","ott","streaming"]):
        s = patterns["subscription_total"]
        detail = ", ".join([f"{k} ₹{v:.0f}" for k,v in patterns["subscription_detail"].items()])
        return (f"You pay **₹{s:,.0f}/month** on subscriptions.\n\n"
                f"Services: {detail}.\n\n"
                f"You have 3 OTT platforms — consider cancelling the cheapest one (Spotify ₹119).")

    elif any(w in q for w in ["weekend","saturday","sunday"]):
        return (f"You spent **₹{weekend:,.0f}** on weekends vs ₹{weekday_spend:,.0f} on weekdays.\n\n"
                f"Weekend spending is {'higher' if weekend > weekday_spend/3 else 'under control'} "
                f"relative to your daily average.\n\n"
                f"Tip: Plan weekend meals at home to cut this by ₹200–300.")

    elif any(w in q for w in ["biggest","largest","most","highest","expensive","single"]):
        top = by_merch.head(1)
        return (f"Your biggest single expense category is **{by_cat.index[0].title()}** (₹{by_cat.iloc[0]:,.0f}).\n\n"
                f"Your highest single merchant is **{top.index[0]}** — ₹{top.iloc[0]:,.0f} total this month.")

    elif any(w in q for w in ["saving","save","potential","opportunity","reduce"]):
        opps = result["savings_opportunities"]
        total_save = sum(o["saving"] for o in opps)
        lines = "\n".join([f"• {o['title']}: ₹{o['saving']:,.0f} — {o['tip']}" for o in opps])
        return (f"You could save **₹{total_save:,.0f}** this month with 3 changes:\n\n{lines}")

    elif any(w in q for w in ["total","overall","how much","spent","spend"]):
        return (f"You spent **₹{total:,.0f}** in total this month (excluding income).\n\n"
                f"Top categories: "
                + ", ".join([f"{k.title()} ₹{v:,.0f}" for k,v in by_cat.head(3).items()]))

    elif any(w in q for w in ["income","salary","credit","earn"]):
        income_rows = df[df["type"]=="Credit"]
        total_income = income_rows["amount"].sum()
        return (f"Your total income this month: **₹{total_income:,.0f}**.\n\n"
                f"After expenses of ₹{total:,.0f}, your net savings this month: "
                f"**₹{total_income - total:,.0f}** ({(total_income-total)/total_income*100:.1f}% savings rate).")

    elif any(w in q for w in ["health","score","grade","rating"]):
        h = result["health_score"]
        return (f"Your budget health score is **{h['score']}/100 — {h['label']}**.\n\n"
                + "\n".join([("✅ " if i["good"] is True else "⚠️ " if i["good"] is None else "❌ ") + i["label"]
                              for i in h["breakdown"]]))

    elif any(w in q for w in ["medical","pharmacy","health","medicine","doctor"]):
        med = by_cat.get("medical", 0)
        return (f"You spent **₹{med:,.0f}** on medical/pharmacy this month.\n\n"
                f"This is a necessary expense — no action needed unless it's recurring.")

    elif any(w in q for w in ["shopping","amazon","flipkart","online"]):
        shop = by_cat.get("shopping", 0)
        return (f"You spent **₹{shop:,.0f}** on online shopping this month.\n\n"
                f"Tip: Use the 24-hour cart rule — wait a day before buying anything above ₹500.")

    else:
        top3 = ", ".join([f"{k.title()} ₹{v:,.0f}" for k,v in by_cat.head(3).items()])
        return (f"Based on your statement, here's a quick summary:\n\n"
                f"• Total spent: ₹{total:,.0f}\n"
                f"• Top 3 categories: {top3}\n"
                f"• Subscriptions: ₹{patterns['subscription_total']:,.0f}/month\n"
                f"• Health score: {result['health_score']['score']}/100\n\n"
                f"Try asking about food, transport, subscriptions, weekend spending, or savings.")


# ── Suggestion Buttons ────────────────────────────────────────────────────────
st.markdown("**Try asking:**")
suggestions = [
    "How much did I spend on food?",
    "What are my subscriptions?",
    "How much did I spend on weekends?",
    "What is my biggest expense?",
    "How much can I save?",
    "What is my health score?",
]
cols = st.columns(3)
for i, q in enumerate(suggestions):
    with cols[i % 3]:
        if st.button(q, use_container_width=True):
            st.session_state["prefill_q"] = q

# ── Input ─────────────────────────────────────────────────────────────────────
prefill  = st.session_state.pop("prefill_q", "")
question = st.text_input(
    "Your question",
    value=prefill,
    placeholder="e.g. How much did I spend on food this month?",
    label_visibility="collapsed"
)

if st.button("Ask →", type="primary") and question.strip():
    answer = answer_from_data(question)
    answer_html = answer.replace("\n", "<br>")
    st.markdown(f'<div class="answer-box"><b>Answer:</b><br><br>{answer_html}</div>',
                unsafe_allow_html=True)

    if "qa_history" not in st.session_state:
        st.session_state["qa_history"] = []
    st.session_state["qa_history"].insert(0, {"q": question, "a": answer})

# ── History ───────────────────────────────────────────────────────────────────
if st.session_state.get("qa_history"):
    st.divider()
    st.subheader("Previous Questions")
    for item in st.session_state["qa_history"][:5]:
        with st.expander(item["q"]):
            st.markdown(item["a"])

st.divider()
if st.button("← Back to Dashboard"):
    st.switch_page("pages/2_Dashboard.py")