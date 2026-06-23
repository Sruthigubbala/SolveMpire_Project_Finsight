import os
from dotenv import load_dotenv

# 1. Load the environment first before ANY LangChain modules try to read it
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage  # Fixed legacy import!

from backend.agents.statement_parser import parse_statement
from backend.agents.pattern_analysis  import analyze_patterns
from backend.agents.advice_agent      import generate_advice_prompt
from backend.agents.product_matcher   import match_schemes_prompt
from backend.agents.calculators       import calculate_savings_opportunities, calculate_health_score
from backend.rag.retriever            import load_retriever

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

def run_finsight_pipeline(file_path: str) -> dict:
    # 2. Try loading retriever safely with a fallback if offline
    try:
        retriever = load_retriever()
    except Exception as e:
        print(f"⚠️ Warning: Embedding retriever could not connect to Hugging Face ({e}). Using offline mode.")
        retriever = None

    df = parse_statement(file_path)
    patterns = analyze_patterns(df)
    
    # 3. Inject mock/fallback text for prompts if retriever is down due to network
    advice = llm.invoke([HumanMessage(content=generate_advice_prompt(patterns, retriever))]).content
    schemes = llm.invoke([HumanMessage(content=match_schemes_prompt(patterns, retriever))]).content
    
    savings_opps = calculate_savings_opportunities(df, patterns)
    health_score = calculate_health_score(df, patterns)

    return {
        "df":                    df,
        "patterns":              patterns,
        "advice":                advice,
        "schemes":               schemes,
        "savings_opportunities": savings_opps,
        "health_score":          health_score,
    }