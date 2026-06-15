# backend/agents/nl_query_agent.py
import os, pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFaceEmbeddings
load_dotenv()
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

def answer_question(question: str, df: pd.DataFrame) -> str:
    by_cat   = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    by_merch = df.groupby("description")["amount"].sum().sort_values(ascending=False).head(15)
    by_day   = df.groupby("weekday")["amount"].sum()
    by_month = df.groupby("month")["amount"].sum()

    context = f"""
Total transactions: {len(df)}
Total spent: ₹{df['amount'].sum():,.0f}
Date range: {df['date'].min().date()} to {df['date'].max().date()}

By Category:
{by_cat.to_string()}

Top Merchants:
{by_merch.to_string()}

By Day of Week:
{by_day.to_string()}

By Month:
{by_month.to_string()}
"""
    prompt = f"""
You are a personal finance assistant. Answer the user's question
using only the data below. Be specific. Use ₹ amounts.
If data is insufficient, say so clearly.

Data:
{context}

Question: {question}
"""
    return llm.invoke(prompt).content