# backend/rag/retriever.py
from backend.rag.vector_store import load_vector_store
from langchain_huggingface import HuggingFaceEmbeddings

_cache = None

def load_retriever():
    global _cache
    if _cache is None:
        _cache = load_vector_store().as_retriever(search_kwargs={"k": 4})
    return _cache

def retrieve(query: str, retriever=None) -> list:
    return (retriever or load_retriever()).invoke(query)