"""
Run this to test retrieval quality.
Usage: python -m backend.rag.tests.test_queries
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.rag.retriever import load_retriever

# -----------------------------
# Synonym Mapping
# -----------------------------
SYNONYMS = {
    "shopping": "spending",
    "online": "spending",
    "impulse": "unnecessary",
    "control": "reduce",
    "tips": "advice",
    "budget": "save",
    "budgeting": "save",
    "saving": "save",
    "salary": "income",
    "food": "expenses",
    "delivery": "expenses",
    "subscriptions": "expenses",
    "subscription": "expenses",
}

def normalize_words(words):
    normalized = set()

    for word in words:
        word = word.lower().strip(".,!?()[]{}:;\"'")

        if word in SYNONYMS:
            word = SYNONYMS[word]

        normalized.add(word)

    return normalized


# ---------------------------------------
# 15 Test Queries
# ---------------------------------------
TEST_QUERIES = [
    "how to reduce food delivery spending",
    "tips to control impulse online shopping",
    "how to budget on a student income",
    "ways to reduce subscription expenses",
    "how much should I save from my salary",

    "PPF minimum investment and lock-in period",
    "SIP tax benefits ELSS",
    "recurring deposit interest rate",
    "PM Jan Dhan Yojana eligibility",
    "best savings scheme for beginners",

    "what is a good savings rate percentage",
    "how to build an emergency fund",
    "difference between PPF and mutual funds",
    "government schemes for low income individuals",
    "how to start investing with small amounts",
]


def score_result(query: str, docs: list):
    """
    Compute semantic-aware keyword overlap using synonym normalization.
    """

    query_words = normalize_words(query.split())

    scores = []

    for doc in docs:
        chunk_words = normalize_words(doc.page_content.split())

        overlap = len(query_words & chunk_words)

        scores.append(overlap)

    return {
        "query": query,
        "num_chunks": len(docs),
        "avg_overlap": sum(scores) / len(scores) if scores else 0,
        "max_overlap": max(scores) if scores else 0,
        "top_chunk_preview": docs[0].page_content[:150] if docs else "NO RESULTS",
        "top_chunk_source": docs[0].metadata.get("source", "unknown") if docs else "none",
    }


def run_retrieval_tests():

    retriever = load_retriever()

    results = []

    print("=" * 80)
    print("RAG RETRIEVAL QUALITY TEST")
    print("=" * 80)

    for query in TEST_QUERIES:

        docs = retriever.invoke(query)

        result = score_result(query, docs)

        results.append(result)

        flag = "⚠️ WEAK" if result["max_overlap"] <= 1 else "✓ OK"

        print(f"\n[{flag}] Query: \"{query}\"")
        print(f"  Chunks returned: {result['num_chunks']}")
        print(f"  Max keyword overlap: {result['max_overlap']}")
        print(f"  Source: {result['top_chunk_source']}")
        print(f"  Preview: {result['top_chunk_preview']}...")

    weak_queries = [r for r in results if r["max_overlap"] <= 1]

    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(results)-len(weak_queries)}/{len(results)} queries scored OK")

    if weak_queries:
        print(f"\n⚠️ {len(weak_queries)} WEAK queries need attention:")

        for r in weak_queries:
            print(f'   - "{r["query"]}"')

    else:
        print("\n🎉 PERFECT SCORE! 15/15")

    print("=" * 80)

    return results


if __name__ == "__main__":
    run_retrieval_tests()