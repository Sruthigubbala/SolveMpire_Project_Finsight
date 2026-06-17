# frontend/components/charts.py
import plotly.graph_objects as go
import streamlit as st

def spending_bar_chart(by_category: dict):
    cats = list(by_category.keys())
    vals = list(by_category.values())
    fig = go.Figure(go.Bar(
        x=vals, y=[c.title() for c in cats],
        orientation="h",
        marker_color="#1E5EFF",
        marker_line_width=0
    ))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_title="Amount (₹)", yaxis_title="",
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        font=dict(family="DM Sans")
    )
    st.plotly_chart(fig, use_container_width=True)

def health_score_display(health: dict):
    score = health["score"]
    label = health["label"]
    color = "#00A86B" if score >= 65 else "#F59E0B" if score >= 45 else "#E5281E"
    st.markdown(f"""
    <div style="text-align:center;padding:16px">
      <div style="font-size:52px;font-weight:700;color:{color}">{score}</div>
      <div style="font-size:16px;color:#64748B">out of 100 — <b>{label}</b></div>
    </div>""", unsafe_allow_html=True)
    st.progress(score / 100)
    st.write("")
    for item in health["breakdown"]:
        icon = "✅" if item["good"] else "⚠️" if item["good"] is None else "❌"
        st.markdown(f"{icon} {item['label']}")