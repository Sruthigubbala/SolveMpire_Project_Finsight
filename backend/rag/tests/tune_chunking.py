# backend/rag/tests/tune_chunking.py
"""
Run this to compare different chunk_size/overlap settings side by side.
Usage: python -m backend.rag.tests.tune_chunking
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "../documents")

# Candidate configs to test
CONFIGS = [
    {"chunk_size": 300, "chunk_overlap": 30},
    {"chunk_size": 500, "chunk_overlap": 50},   # current default
    {"chunk_size": 800, "chunk_overlap": 100},
]

TEST_QUERIES = [
    "how to reduce food delivery spending",
    "PPF minimum investment lock-in",
    "SIP tax benefits",
    "emergency fund savings rate",
]

def load_raw_docs():
    docs = []
    for f in os.listdir(DOCS_FOLDER):
        if f.endswith(".pdf"):
            docs.extend(PyPDFLoader(os.path.join(DOCS_FOLDER, f)).load())
    return docs

def test_config(raw_docs, config, embeddings):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(raw_docs)
    vs = FAISS.from_documents(chunks, embeddings)
    retriever = vs.as_retriever(search_kwargs={"k": 4})

    total_overlap = 0
    for query in TEST_QUERIES:
        docs = retriever.invoke(query)
        query_words = set(query.lower().split())
        for doc in docs:
            chunk_words = set(doc.page_content.lower().split())
            total_overlap += len(query_words & chunk_words)

    return {
        "config": config,
        "num_chunks": len(chunks),
        "avg_chunk_len": sum(len(c.page_content) for c in chunks) / len(chunks),
        "total_relevance_score": total_overlap,
    }

def run_comparison():
    print("=" * 70)
    print("CHUNKING CONFIGURATION COMPARISON")
    print("=" * 70)

    raw_docs = load_raw_docs()
    print(f"Loaded {len(raw_docs)} pages from source PDFs\n")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    results = []

    for config in CONFIGS:
        print(f"Testing chunk_size={config['chunk_size']}, overlap={config['chunk_overlap']}...")
        result = test_config(raw_docs, config, embeddings)
        results.append(result)
        print(f"  → {result['num_chunks']} chunks, "
              f"avg length {result['avg_chunk_len']:.0f} chars, "
              f"relevance score {result['total_relevance_score']}\n")

    best = max(results, key=lambda r: r["total_relevance_score"])
    print("=" * 70)
    print(f"BEST CONFIG: chunk_size={best['config']['chunk_size']}, "
          f"overlap={best['config']['chunk_overlap']}")
    print(f"(relevance score: {best['total_relevance_score']})")
    print("=" * 70)
    print("\n→ If this differs from chunker.py's current settings, update chunker.py")
    print("  then rebuild the index with vector_store.py's build_vector_store()")

    return best

if __name__ == "__main__":
    run_comparison()