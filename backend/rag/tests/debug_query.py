from backend.rag.retriever import retrieve

query = "tips to control impulse online shopping"

docs = retrieve(query)

print("=" * 80)
print("Retrieved Documents")
print("=" * 80)

for i, doc in enumerate(docs, 1):
    print(f"\nDocument {i}")
    print("Source:", doc.metadata.get("source"))
    print("-" * 60)
    print(doc.page_content)
    print("-" * 60)