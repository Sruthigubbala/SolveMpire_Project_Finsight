# backend/agents/advice_agent.py

def generate_advice_prompt(patterns: dict, retriever) -> str:
    query = "financial planning rules for budgeting savings rate and subscription tracking"

    docs = retriever.invoke(query) if retriever else []
    context = "\n".join([d.page_content for d in docs])

    # Build a readable breakdown of top spending categories
    cat_lines = "\n".join(
        f"    • {cat.replace('_', ' ').title()}: ₹{amt:,.0f}"
        for cat, amt in list(patterns.get("by_category", {}).items())[:8]
    )

    sub_lines = "\n".join(
        f"    • {name}: ₹{amt:,.0f}"
        for name, amt in list(patterns.get("subscription_detail", {}).items())[:5]
    )

    return f"""
You are a personal wealth manager. Analyse the user's spending data below and produce
a clear, structured Action Plan.

════════════════════════════════════════════════════════════
FORMATTING RULES — follow these exactly:
════════════════════════════════════════════════════════════
1.  Use exactly FIVE numbered sections with the headings below.
2.  Under each section write 2–4 bullet points (start with •).
3.  Leave ONE blank line between every bullet point so they are easy to read.
4.  Every bullet must contain a specific ₹ amount or % figure from the data.
5.  End with a one-line "Bottom Line" summary.
6.  Do NOT write walls of text. Keep each bullet to 1–2 sentences max.

════════════════════════════════════════════════════════════
REQUIRED SECTIONS:
════════════════════════════════════════════════════════════

1. 🔴 Immediate Actions  (things to fix this week)

2. 📊 Spending Patterns  (what the numbers reveal)

3. 💡 Savings Opportunities  (where money can be saved)

4. 📅 Monthly Budget Targets  (suggested limits per category)

5. 🚀 Long-term Steps  (investments & financial growth)

════════════════════════════════════════════════════════════
USER SPENDING DATA:
════════════════════════════════════════════════════════════

Total Spent        : ₹{patterns.get('total_spent', 0):,.0f}
Weekend Spend      : ₹{patterns.get('weekend_spend', 0):,.0f}
Subscription Total : ₹{patterns.get('subscription_total', 0):,.0f}
Top Category       : {patterns.get('top_category', 'N/A').replace('_', ' ').title()}
Transaction Count  : {patterns.get('transaction_count', 0)}

Spending by Category:
{cat_lines if cat_lines else '    No category breakdown available.'}

Subscriptions Detected:
{sub_lines if sub_lines else '    No subscriptions detected.'}

Monthly Trend:
{chr(10).join(f"    • {m}: ₹{v:,.0f}" for m, v in patterns.get('monthly_trend', {}).items())}

════════════════════════════════════════════════════════════
KNOWLEDGE BASE GUIDELINES:
════════════════════════════════════════════════════════════
{context if context else "Standard 50/30/20 budgeting rule: 50% needs, 30% wants, 20% savings."}

Now write the Action Plan following the formatting rules above.
"""