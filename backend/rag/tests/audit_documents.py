# backend/rag/tests/audit_documents.py
"""
Run this to audit what documents are loaded into the RAG pipeline.
Usage: python -m backend.rag.tests.audit_documents
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.rag.chunker import load_and_chunk

DOCS_FOLDER = os.path.join(os.path.dirname(__file__), "../documents")

REQUIRED_TOPICS = {
    "RBI financial literacy":   ["rbi", "literacy", "financial"],
    "NSE investor basics":      ["nse", "investor", "equity", "market"],
    "PPF scheme":               ["ppf", "provident"],
    "AMFI mutual funds / SIP":  ["amfi", "mutual", "sip"],
    "PM Jan Dhan Yojana":       ["jan dhan", "jandhan"],
}

def audit():
    print("=" * 70)
    print("DOCUMENT AUDIT")
    print("=" * 70)

    if not os.path.exists(DOCS_FOLDER):
        print(f"✗ Folder missing: {DOCS_FOLDER}")
        return

    pdfs = [f for f in os.listdir(DOCS_FOLDER) if f.endswith(".pdf")]
    print(f"\nPDFs found in {DOCS_FOLDER}: {len(pdfs)}")
    for p in pdfs:
        size_kb = os.path.getsize(os.path.join(DOCS_FOLDER, p)) / 1024
        print(f"  - {p} ({size_kb:.0f} KB)")

    if len(pdfs) < 4:
        print(f"\n⚠️  Only {len(pdfs)} PDFs — spec requires minimum 4. Add more before Week 4.")

    print("\nLoading and chunking to verify content...")
    chunks = load_and_chunk(DOCS_FOLDER)
    print(f"Total chunks produced: {len(chunks)}")

    all_text = " ".join([c.page_content.lower() for c in chunks])

    print("\n" + "-" * 70)
    print("TOPIC COVERAGE CHECK")
    print("-" * 70)
    for topic, keywords in REQUIRED_TOPICS.items():
        found = any(kw in all_text for kw in keywords)
        flag = "✓" if found else "✗ MISSING"
        print(f"{flag}  {topic}")
        if not found:
            print(f"     → None of {keywords} found in any document. Add a source PDF for this.")

    print("\n" + "=" * 70)
    avg_len = sum(len(c.page_content) for c in chunks) / len(chunks) if chunks else 0
    print(f"Average chunk length: {avg_len:.0f} characters")
    if avg_len < 200:
        print("⚠️  Chunks seem very short — context may be too fragmented (see Step 4)")
    print("=" * 70)

if __name__ == "__main__":
    audit()