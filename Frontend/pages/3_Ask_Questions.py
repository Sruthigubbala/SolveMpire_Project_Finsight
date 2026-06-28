# Frontend/pages/3_Ask_Questions.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Ask Questions | FinSight", layout="wide")

# ── Guard ──────────────────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.warning("No analysis found. Please upload a statement first.")
    if st.button("Go to Upload"):
        st.switch_page("pages/1_upload.py")
    st.stop()

result   = st.session_state["result"]
df       = result["df"]
patterns = result["patterns"]

# ── Gemini setup ───────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY not found in .env file. Please add it.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

# ── Build financial context from user's data ───────────────────────────────────
def build_context() -> str:
    """Convert the analysed result into a plain-text context for the LLM."""
    # Normalise column names
    col_map    = {c.lower().replace(" ", "_"): c for c in df.columns}
    type_col   = col_map.get("type") or col_map.get("transaction_type")
    amount_col = col_map.get("amount") or col_map.get("amount_(inr)")
    cat_col    = col_map.get("category")
    desc_col   = col_map.get("description") or col_map.get("narration")

    if type_col and type_col in df.columns:
        debits  = df[df[type_col].astype(str).str.lower().isin(["debit", "dr"])]
        credits = df[df[type_col].astype(str).str.lower().isin(["credit", "cr"])]
    else:
        debits  = df
        credits = df.iloc[0:0]

    total_spent  = debits[amount_col].sum()  if amount_col else 0
    total_income = credits[amount_col].sum() if amount_col else 0
    net_savings  = total_income - total_spent

    # Category breakdown
    cat_lines = ""
    if cat_col and cat_col in df.columns and amount_col:
        by_cat = debits.groupby(cat_col)[amount_col].sum().sort_values(ascending=False)
        cat_lines = "\n".join([f"  - {k}: ₹{v:,.0f}" for k, v in by_cat.items()])

    # Subscription detail
    subs = patterns.get("subscription_detail", {})
    sub_lines = "\n".join([f"  - {k}: ₹{v:,.0f}/month" for k, v in subs.items()]) or "  None detected"

    # Savings opportunities
    opps = result.get("savings_opportunities", [])
    opp_lines = "\n".join([f"  - {o['title']}: save ₹{o['saving']:,.0f} — {o['tip']}" for o in opps]) or "  None"

    # Health score
    health  = result.get("health_score", {})
    h_score = health.get("score", "?")
    h_label = health.get("label", "?")

    # Recent transactions (top 20 for context)
    tx_preview = ""
    if desc_col and amount_col and type_col and all(c in df.columns for c in [desc_col, amount_col, type_col]):
        rows = df[[desc_col, amount_col, type_col]].head(20)
        tx_preview = rows.to_string(index=False)

    context = f"""
You are FinSight AI, a helpful personal finance assistant. You have full access to this user's bank statement analysis. Answer their questions accurately using the data below. Be concise, friendly, and give actionable advice where relevant. Use ₹ for currency. Format numbers clearly.

=== USER'S FINANCIAL SUMMARY ===
Total Income This Month : ₹{total_income:,.0f}
Total Spent This Month  : ₹{total_spent:,.0f}
Net Savings             : ₹{net_savings:,.0f}
Savings Rate            : {net_savings/total_income*100:.1f}% of income
Budget Health Score     : {h_score}/100 ({h_label})
Weekend Spending        : ₹{patterns.get('weekend_spend', 0):,.0f}
Total Transactions      : {patterns.get('transaction_count', len(df))}

=== SPENDING BY CATEGORY ===
{cat_lines or '  Data not available'}

=== SUBSCRIPTIONS ===
Total: ₹{patterns.get('subscription_total', 0):,.0f}/month
{sub_lines}

=== SAVINGS OPPORTUNITIES IDENTIFIED ===
{opp_lines}

=== RECENT TRANSACTIONS (sample) ===
{tx_preview or '  Not available'}
"""
    return context.strip()


SYSTEM_CONTEXT = build_context()

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Page */
.block-container { padding-top: 1.5rem !important; }

/* Chat container */
.chat-wrapper {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 8px 0 80px 0;
}

/* Bubbles */
.bubble {
    max-width: 72%;
    padding: 12px 16px;
    border-radius: 18px;
    font-size: 15px;
    line-height: 1.65;
    word-wrap: break-word;
}
.bubble-user {
    background: #1E5EFF;
    color: #ffffff;
    border-bottom-right-radius: 4px;
    align-self: flex-end;
    margin-left: auto;
}
.bubble-ai {
    background: #F1F5F9;
    color: #1E293B;
    border-bottom-left-radius: 4px;
    align-self: flex-start;
}
.bubble-row {
    display: flex;
    flex-direction: column;
}
.bubble-row-user { align-items: flex-end; }
.bubble-row-ai   { align-items: flex-start; }

.avatar {
    font-size: 20px;
    margin-bottom: 4px;
}

/* Suggestion chips */
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0 4px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("💬 Ask About Your Statement")
st.caption("Powered by Gemini · Ask anything about your transactions, spending, or savings")
st.divider()

# ── Session init ───────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []   # list of {"role": "user"/"ai", "text": str}
if "gemini_session" not in st.session_state:
    # Start a Gemini chat session with the financial context as first message
    chat = model.start_chat(history=[])
    # Prime the model with the context
    chat.send_message(
        f"[SYSTEM CONTEXT — do not repeat this to the user]\n{SYSTEM_CONTEXT}\n\n"
        "Acknowledge that you have read the context by saying only: 'Ready'"
    )
    st.session_state["gemini_session"] = chat

# ── Render chat history ────────────────────────────────────────────────────────
if st.session_state["chat_history"]:
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"""
<div class="bubble-row bubble-row-user">
  <div class="avatar" style="text-align:right">🧑</div>
  <div class="bubble bubble-user">{msg['text']}</div>
</div>""", unsafe_allow_html=True)
        else:
            # Convert markdown **bold** and newlines for HTML display
            text_html = (msg["text"]
                         .replace("&", "&amp;")
                         .replace("<", "&lt;")
                         .replace(">", "&gt;")
                         .replace("\n", "<br>"))
            import re
            text_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text_html)
            st.markdown(f"""
<div class="bubble-row bubble-row-ai">
  <div class="avatar">🤖</div>
  <div class="bubble bubble-ai">{text_html}</div>
</div>""", unsafe_allow_html=True)
else:
    # Welcome message
    st.markdown("""
<div class="bubble-row bubble-row-ai">
  <div class="avatar">🤖</div>
  <div class="bubble bubble-ai">
    Hi! I've analysed your bank statement. Ask me anything — your spending, savings, subscriptions, or how to improve your finances. 💰
  </div>
</div>""", unsafe_allow_html=True)

# ── Suggestion chips ───────────────────────────────────────────────────────────
suggestions = [
    "How much did I spend on food?",
    "What are my subscriptions?",
    "What is my biggest expense?",
    "How much can I save?",
    "How much did I spend on weekends?",
    "What is my health score?",
]

cols = st.columns(3)
for i, q in enumerate(suggestions):
    with cols[i % 3]:
        if st.button(q, use_container_width=True, key=f"chip_{i}"):
            st.session_state["pending_question"] = q
            st.rerun()

st.divider()

# ── Handle pending question (from chips) ───────────────────────────────────────
if "pending_question" in st.session_state:
    pending = st.session_state.pop("pending_question")
    with st.spinner("Thinking..."):
        try:
            response = st.session_state["gemini_session"].send_message(pending)
            ai_reply = response.text.strip()
        except Exception as e:
            ai_reply = f"Sorry, I ran into an error: {str(e)}"
    st.session_state["chat_history"].append({"role": "user", "text": pending})
    st.session_state["chat_history"].append({"role": "ai",   "text": ai_reply})
    st.rerun()

# ── Text input + send ──────────────────────────────────────────────────────────
with st.container():
    col_input, col_btn = st.columns([6, 1])
    with col_input:
        user_input = st.text_input(
            "Message",
            placeholder="Type your question here…",
            label_visibility="collapsed",
            key="chat_input"
        )
    with col_btn:
        send = st.button("Send →", type="primary", use_container_width=True)

if send and user_input.strip():
    question = user_input.strip()
    with st.spinner("Thinking..."):
        try:
            response = st.session_state["gemini_session"].send_message(question)
            ai_reply = response.text.strip()
        except Exception as e:
            ai_reply = f"Sorry, I ran into an error: {str(e)}"
    st.session_state["chat_history"].append({"role": "user", "text": question})
    st.session_state["chat_history"].append({"role": "ai",   "text": ai_reply})
    st.rerun()

# ── Clear chat ─────────────────────────────────────────────────────────────────
col_clear, col_back = st.columns([1, 5])
with col_clear:
    if st.button("🗑 Clear Chat"):
        st.session_state["chat_history"] = []
        chat = model.start_chat(history=[])
        chat.send_message(
            f"[SYSTEM CONTEXT — do not repeat this to the user]\n{SYSTEM_CONTEXT}\n\n"
            "Acknowledge that you have read the context by saying only: 'Ready'"
        )
        st.session_state["gemini_session"] = chat
        st.rerun()
with col_back:
    if st.button("← Back to Dashboard"):
        st.switch_page("pages/2_Dashboard.py")