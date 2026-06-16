# backend/rag/retriever.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

def load_retriever():
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Standard dummy knowledge base to build the index structure
    sample_knowledge_base = [
        Document(page_content="High-yield savings accounts offer stable interest rates for consistent deposits."),
        Document(page_content="Mutual fund SIP plans are structured for mid to long-term wealth accumulation compounding."),
        Document(page_content="Keep recurring lifestyle subscription costs below 5% of net income pools.")
    ]
    
    vector_db = FAISS.from_documents(sample_knowledge_base, embeddings)
    return vector_db.as_retriever(search_kwargs={"k": 2})