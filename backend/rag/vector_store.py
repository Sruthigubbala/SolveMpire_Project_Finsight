# backend/rag/vector_store.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from backend.rag.chunker import load_and_chunk

PATH = "backend/rag/faiss_index"

def build_vector_store():
    chunks     = load_and_chunk()
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vs         = FAISS.from_documents(chunks, embeddings)
    vs.save_local(PATH)
    print(f"Saved FAISS index to {PATH}")

def load_vector_store():
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.load_local(PATH, embeddings, allow_dangerous_deserialization=True)