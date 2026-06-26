# backend/rag/tests/verify_agent_context.py
"""
Run this to confirm agent prompts are correctly injecting retrieved context.
Usage: python -m backend.rag.tests.verify_agent_context
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.agents.advice_agent import generate_advice_prompt
from backend.agents.product_matcher import match_schemes_prompt
from backend.rag.retriever import load_retriever

# Fake patterns dict mimicking real output from pattern_analysis.py
FAKE_PATTERNS = {
    "total_spent": 18500,
    "by_category": {"food": 6200, "shopping": 4100, "subscriptions": 1467, "transport": 2100},
    "weekend_spend": 7800,
    "subscription_total": 1467,
    "top_category": "food",
}

def verify_advice_agent(retriever):
    print("=" * 70)
    print("ADVICE AGENT — context injection check")
    print("=" * 70)
    prompt = generate_advice_prompt(FAKE_PATTERNS, retriever)
    print(prompt)

    has_context = (
    "KNOWLEDGE BASE GUIDELINES" in prompt
    or "Knowledge base" in prompt
    or "Relevant advice" in prompt
)
    has_data = "₹6200" in prompt or "₹6,200" in prompt or "food" in prompt.lower()
    print("\n--- CHECKS ---")
    print(f"{'✓' if has_context else '✗'} Retrieved context section present")
    print(f"{'✓' if has_data else '✗'} User's actual spending numbers present")

def verify_product_matcher(retriever):
    print("\n" + "=" * 70)
    print("PRODUCT MATCHER — context injection check")
    print("=" * 70)
    prompt = match_schemes_prompt(FAKE_PATTERNS, retriever)
    print(prompt)

    has_context = (
    "Context:" in prompt
    or "knowledge base context" in prompt.lower()
)
    has_savings = "savings potential" in prompt.lower() or "₹" in prompt
    print("\n--- CHECKS ---")
    print(f"{'✓' if has_context else '✗'} Retrieved context section present")
    print(f"{'✓' if has_savings else '✗'} Calculated savings potential present")

def run_verification():
    retriever = load_retriever()
    verify_advice_agent(retriever)
    verify_product_matcher(retriever)

    print("\n" + "=" * 70)
    print("NOTE: This only checks PROMPT construction, not Gemini's final output.")
    print("To check the full output, run Step 6 (run_full_pipeline.py) which")
    print("actually calls Gemini and prints the generated advice/schemes text.")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()