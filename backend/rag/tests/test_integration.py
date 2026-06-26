# test_integration.py
from backend.rag.retriever import retrieve

print("INTEGRATION TEST")
print("="*50)

# AGENT 3 TEST — Advice Agent
print("\nAgent 3 — Advice Agent Test:")
spending = "User spent Rs.8000 on food this month"
query = f"advice for reducing spending: {spending}"
results = retrieve(query)
print(f"Chunks returned: {len(results)}")
print(f"Source: {results[0].metadata.get('source')}")
print(f"Preview: {results[0].page_content[:150]}")
print("✅ Agent 3 working!" if len(results) > 0 
      else "❌ Agent 3 FAILED")

# AGENT 4 TEST — Product Matcher
print("\nAgent 4 — Product Matcher Test:")
profile = "monthly savings Rs.3000, wants tax saving"
query = f"best government scheme for: {profile}"
results = retrieve(query)
print(f"Chunks returned: {len(results)}")
print(f"Source: {results[0].metadata.get('source')}")
print(f"Preview: {results[0].page_content[:150]}")
print("✅ Agent 4 working!" if len(results) > 0 
      else "❌ Agent 4 FAILED")