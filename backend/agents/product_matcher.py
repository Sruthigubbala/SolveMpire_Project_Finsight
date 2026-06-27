def match_schemes_prompt(patterns: dict, retriever) -> str:
    potential = patterns["total_spent"] * 0.15
    query = f"Government savings schemes SIPs RD for someone saving ₹{potential:.0f}/month"
    
    # LangChain retrievers natively use .invoke() to fetch relevant documents
    docs = retriever.invoke(query) if retriever else []
    
    context = "\n".join([d.page_content for d in docs])
    
    return f"""
You are a financial advisor matching government or banking schemes to user patterns.
Using the following knowledge base context, recommend matching products.

Context:
{context}

User Profile:
- Monthly Expenditure: ₹{patterns['total_spent']}
- Estimated Investment Budget: ₹{potential:.0f}/month
"""# backend/agents/product_matcher.py

def match_schemes_prompt(patterns: dict, retriever) -> str:
    total_spent   = patterns["total_spent"]
    sub_total     = patterns["subscription_total"]
    top_category  = patterns["top_category"]
    invest_budget = round(total_spent * 0.15, 0)
    by_cat        = patterns["by_category"]

    cat_summary = ", ".join(
        [f"{cat}: ₹{amt:,.0f}" for cat, amt in list(by_cat.items())[:5]]
    )

    # Dynamic RAG query based on actual user profile
    if invest_budget < 500:
        query = "savings schemes very low income zero balance RD ₹100 India"
    elif invest_budget < 2000:
        query = f"savings schemes SIP RD ₹{invest_budget:.0f} per month low income India"
    elif sub_total > 1000:
        query = f"ELSS tax saving SIP ₹{invest_budget:.0f} high subscription spender India"
    elif top_category in ["food", "shopping"]:
        query = f"recurring deposit PPF disciplined saving impulsive spender ₹{invest_budget:.0f}"
    else:
        query = f"SIP PPF NPS best schemes ₹{invest_budget:.0f} per month India"

    # Use .invoke() directly — compatible with LangChain retrievers
    docs    = retriever.invoke(query) if retriever else []
    context = "\n".join([d.page_content for d in docs])

    return f"""
You are a certified Indian financial advisor. Based ONLY on this specific user's data,
recommend EXACTLY 2–3 savings schemes that best match their profile.

USER PROFILE:
- Total monthly spend: ₹{total_spent:,.0f}
- Estimated investable surplus: ₹{invest_budget:,.0f}/month (15% of spend)
- Top spending category: {top_category}
- Monthly subscriptions: ₹{sub_total:,.0f}
- Spending breakdown: {cat_summary}

RULES:
1. Only recommend schemes whose minimum investment is ≤ ₹{invest_budget:,.0f}.
2. If surplus < ₹500 → prioritize zero-balance/low-entry schemes (PMJDY, RD ₹100).
3. If surplus ₹500–₹2000 → prioritize RD, PPF, small SIPs.
4. If surplus > ₹2000 → include ELSS/SIP + PPF/NPS for tax benefit.
5. If top category is food/shopping → include one scheme that builds spending discipline.
6. Each recommendation must explain WHY it suits THIS user's actual numbers.

For each scheme provide:
- Scheme name and type
- Why it suits THIS user (reference their actual spend figures)
- Suggested monthly amount (must be ≤ ₹{invest_budget:,.0f})
- Expected return and lock-in period

Relevant knowledge base:
{context}
"""