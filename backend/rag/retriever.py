from backend.rag.vector_store import load_vector_store

# Global cache
_cache = None


def load_retriever():
    """
    Load the FAISS retriever only once and reuse it.
    """
    global _cache

    if _cache is None:
        print("Loading retriever from FAISS...")

        vector_store = load_vector_store()

        _cache = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 8,
                "fetch_k": 20,
                "lambda_mult": 0.7
            }
        )

        print("Retriever loaded successfully!")

    else:
        print("Loading from cache...")

    return _cache


def retrieve(query: str):
    """
    Retrieve relevant documents for a user query.
    """
    retriever = load_retriever()
    return retriever.invoke(query)