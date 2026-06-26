import streamlit as st

st.set_page_config(page_title="About | FinSight", layout="wide")

st.title("About FinSight")
st.caption("PROJECT 04 · SolveMpire · Team 4")

st.markdown("""
FinSight is an agentic AI personal finance coach. It reads your bank statement,
identifies behavioral spending patterns using multi-agent AI, and gives you a
personalized action plan backed by real documents from RBI and NSE —
not generic financial advice.
""")

st.divider()

# ── Agent Architecture ────────────────────────────────────────────────────────
st.subheader("Agent Architecture")
st.code("""
User uploads CSV / PDF
        │
        ▼
[Agent 1 — Statement Parser]
  Reads file → categorizes every transaction (food, transport, subs...)
        │
        ▼
[Agent 2 — Pattern Analysis]
  Finds: top categories, weekend spend, subscriptions, monthly trends
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
[Agent 3 — Advice Agent]         [Agent 4 — Product Matcher]
  RAG over RBI financial           RAG over NSE / PM savings
  literacy documents               scheme documents
  → Gemini: 3–5 specific           → Gemini: SIPs / PPF / RD
    action steps                     recommendations
        │                                      │
        └──────────────┬───────────────────────┘
                       ▼
          [Agent 5 — NL Query Agent]
            Answers plain-English questions
            about the user's transactions
                       │
                       ▼
            [Streamlit Frontend]
     Dashboard · Q&A · Schemes · Health Score
""", language=None)

st.divider()

# ── Tech Stack ────────────────────────────────────────────────────────────────
st.subheader("Tech Stack")
st.dataframe([
    {"Layer": "LLM",             "Technology": "Gemini 2.5 Flash",         "Purpose": "Pattern interpretation and advice generation"},
    {"Layer": "RAG Framework",   "Technology": "LangChain",                "Purpose": "Financial literacy and scheme document retrieval"},
    {"Layer": "Vector Store",    "Technology": "FAISS",                    "Purpose": "Embeddings of RBI / NSE financial documents"},
    {"Layer": "Agent Framework", "Technology": "LangChain AgentExecutor",  "Purpose": "Multi-agent orchestration"},
    {"Layer": "Data Processing", "Technology": "Pandas + Python",          "Purpose": "CSV / PDF parsing, categorization, analysis"},
    {"Layer": "Frontend",        "Technology": "Streamlit",                "Purpose": "Upload UI, charts, advice display"},
    {"Layer": "Deployment",      "Technology": "Streamlit Cloud",          "Purpose": "Free public URL"},
], hide_index=True, use_container_width=True)

st.divider()

# ── Team ──────────────────────────────────────────────────────────────────────
st.subheader("Team 4")
st.dataframe([
    {"Member": "Sruthi Gubbala",            "Role": "Team Lead / Member 1",
     "Owns": "All 5 agents + orchestrator + Streamlit Cloud deployment"},
    {"Member": "Devi Maricharla",           "Role": "Member 2",
     "Owns": "RAG pipeline — PDF documents, chunking, FAISS index"},
    {"Member": "Nagulapalli Chandrasekhar", "Role": "Member 3",
     "Owns": "Streamlit frontend — all pages, charts, components"},
], hide_index=True, use_container_width=True)

st.divider()
st.link_button("GitHub Repository ↗", "https://github.com/your-repo-here")