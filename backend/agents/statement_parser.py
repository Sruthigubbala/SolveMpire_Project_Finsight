# backend/agents/statement_parser.py
import pandas as pd
try:
    import pdfplumber
except ImportError:
    pdfplumber = None
import re
CATEGORIES = {
    "food":          ["zomato","swiggy","restaurant","cafe","dominos","kfc"],
    "transport":     ["uber","ola","petrol","fuel","metro","rapido","irctc"],
    "subscriptions": ["netflix","spotify","amazon prime","hotstar","youtube","zee5"],
    "shopping":      ["amazon","flipkart","myntra","meesho","ajio","nykaa"],
    "utilities":     ["electricity","water","internet","broadband","airtel","bsnl"],
    "medical":       ["pharmacy","hospital","clinic","medplus","apollo"],
    "savings":       ["fd","sip","ppf","investment","mutual fund","rd account"],
    "education":     ["udemy","coursera","college","fees","books"],
}

def categorize(desc: str) -> str:
    desc = desc.lower()
    for cat, kws in CATEGORIES.items():
        if any(k in desc for k in kws):
            return cat
    return "other"

def parse_pdf_statement(path: str) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            matches = re.findall(
                r'(\d{2}[-/]\d{2}[-/]\d{4})\s+(.+?)\s+([\d,]+\.\d{2})', text)
            for m in matches:
                rows.append({"date": m[0], "description": m[1], "amount": m[2]})
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("Could not extract transactions. Try CSV format.")
    return df

def parse_statement(path: str) -> pd.DataFrame:
    if path.endswith(".pdf"):
        df = parse_pdf_statement(path)
    else:
        df = pd.read_csv(path)
        df.columns = [c.strip().lower() for c in df.columns]
    df["category"] = df["description"].apply(categorize)
    df["amount"]   = (df["amount"].astype(str).str.replace(",", "")
                      .apply(pd.to_numeric, errors="coerce").abs())
    df["date"]     = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df["weekday"]  = df["date"].dt.day_name()
    df["month"]    = df["date"].dt.to_period("M").astype(str)
    return df.dropna(subset=["amount"])