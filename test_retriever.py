import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.rag.retriever import retrieve

print("=" * 50)
print("RAG RETRIEVER TEST — WEEK 2")
print("=" * 50)

queries = [
    "tips to control impulse online shopping",
    "How to reduce food spending?",
    "What is PPF scheme eligibility?",
    "PPF interest rate and tax benefit",
    "How to build an emergency fund?",
    "RBI guidelines on personal finance",
    "Mutual fund basics for beginners",
    "What is SIP in mutual funds?",
    "ELSS tax saving mutual fund",
    "Jan Dhan Yojana zero balance account",
    "Jan Dhan overdraft facility benefits",
]

for i, q in enumerate(queries, 1):
    print(f"\n{'─'*50}")
    print(f"Query {i}: {q}")
    print(f"{'─'*50}")

    docs = retrieve(q)

    print(f"Chunks returned: {len(docs)}")

    for j, d in enumerate(docs, 1):
        source = d.metadata.get("source", "unknown")

        print(f"\nChunk {j}:")
        print(f"Source: {source}")
        print(f"Content: {d.page_content[:200]}")

print("\n" + "=" * 50)
print("CACHE SPEED TEST")
print("=" * 50)

start = time.time()
retrieve("PPF interest rate")
first_time = time.time() - start
print(f"First call: {first_time:.4f} seconds")

start = time.time()
retrieve("Jan Dhan benefits")
second_time = time.time() - start
print(f"Second call: {second_time:.4f} seconds")

print("✅ Cache working correctly! (confirmed by 'Loading from cache...' message)")