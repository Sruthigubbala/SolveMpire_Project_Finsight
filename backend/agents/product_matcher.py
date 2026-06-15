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
"""