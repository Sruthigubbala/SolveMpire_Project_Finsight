# backend/rag/chunker.py
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

def load_and_chunk(docs_folder="backend/rag/documents") -> list:
    all_docs = []
    for f in os.listdir(docs_folder):
        if f.endswith(".pdf"):
            file_path = os.path.join(docs_folder, f)
            print(f"Processing: {f}")  # This will print the filename
            try:
                all_docs.extend(PyPDFLoader(file_path).load())
            except Exception as e:
                print(f"❌ ERROR reading file {f}: {e}")

    
        

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(all_docs)
    print(f"Total chunks: {len(chunks)}")
    return chunks
