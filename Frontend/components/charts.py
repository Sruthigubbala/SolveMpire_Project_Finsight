import pandas as pd
import plotly.express as px
import streamlit as st
def spending_bar_chart(category_data):
    """
    Displays a donut chart for spending by category.
    """
    # Convert dictionary to DataFrame
    df = pd.DataFrame({
        "Category": list(category_data.keys()),
        "Amount": list(category_data.values())
    })

    fig = px.pie(
        df,
        names="Category",
        values="Amount",
        hole=0.60,
        color="Category",
        color_discrete_sequence=px.colors.sequential.Blues_r
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>₹%{value:,.0f}<extra></extra>"
    )

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=True,
        legend_title="Category",
        margin=dict(l=20, r=20, t=30, b=20),
        font=dict(
            family="Inter",
            size=14,
            color="#1E293B"
        ),
        height=450
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