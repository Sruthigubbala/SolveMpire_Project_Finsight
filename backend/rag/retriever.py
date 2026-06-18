# backend/rag/retriever.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

_cache = None
_embeddings = None

def load_retriever():
    global _cache, _embeddings

    if _cache is not None:
        print("Loading from cache...")
        return _cache

    print("Loading fresh from disk...")
    _embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

    index_path = "backend/rag/faiss_index"
    vector_db = FAISS.load_local(
        index_path,
        _embeddings,
        allow_dangerous_deserialization=True
    )

    _cache = vector_db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 10}
    )
    return _cache

def retrieve(query: str):
    retriever = load_retriever()
    docs = retriever.invoke(query)
    return docs