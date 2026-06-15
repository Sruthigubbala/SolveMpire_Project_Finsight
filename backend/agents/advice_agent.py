# backend/agents/advice_agent.py

def generate_advice_prompt(patterns: dict, retriever) -> str:
    query = "financial planning rules for budgeting savings rate and subscription tracking"
    
    # Use native invoke here too!
    docs = retriever.invoke(query) if retriever else []
    
    context = "\n".join([d.page_content for d in docs])
    
    return f"""
You are a personal wealth manager. Provide high-level tactical advice based on these patterns.

Context Guidelines:
{context}

User Data Breakdowns:
{patterns}
"""