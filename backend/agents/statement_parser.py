# backend/agents/statement_parser.py
import pandas as pd
import pdfplumber, re

CATEGORIES = {
    "food":          ["zomato","swiggy","restaurant","cafe","dominos","kfc"],
    "transport":     ["uber","ola","petrol","fuel","metro","rapido","irctc","indian oil"],
    "subscriptions": ["netflix","spotify","amazon prime","hotstar","youtube","zee5"],
    "shopping":      ["amazon","flipkart","myntra","meesho","ajio","nykaa"],
    "utilities":     ["electricity","water","internet","broadband","airtel","bsnl","jio"],
    "medical":       ["pharmacy","hospital","clinic","medplus","apollo"],
    "savings":       ["fd","sip","ppf","investment","mutual fund","rd account"],
    "education":     ["udemy","coursera","college","fees","books"],
    "rent":          ["rent"],
}

def categorize(desc: str) -> str:
    desc = desc.lower()
    for cat, kws in CATEGORIES.items():
        if any(k in desc for k in kws):
            return cat
    return "other"


def parse_pdf_statement(path: str) -> pd.DataFrame:
    """
    Handles bank statements formatted as a table:
    Date | Description | Category | Debit (Rs.) | Credit (Rs.) | Balance (Rs.)

    Uses pdfplumber's table extraction (extract_table) instead of a
    free-text regex. Regex line-matching is fragile against this format —
    it silently dropped rows containing em-dashes (e.g. "Salary Credit —
    TCS Ltd") and mis-split multi-word category/description boundaries
    (e.g. "House Rent Transfer" + category "Rent" collapsing into
    "House  Transfer"). Table extraction reads actual column boundaries
    instead of guessing from spacing, so it doesn't have these failure modes.
    """
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                if row is None or len(row) < 6:
                    continue
                date_str, desc, category, debit, credit, balance = [
                    (c or "").strip() for c in row[:6]
                ]

                # Skip header row and the Opening Balance row
                if date_str.lower() in ("date", "") or "opening balance" in desc.lower():
                    continue
                if not re.match(r'^\d{2}-[A-Za-z]{3}-\d{2}$', date_str):
                    continue

                debit_clean  = debit.replace(",", "").replace("-", "").strip()
                credit_clean = credit.replace(",", "").replace("-", "").strip()

                if debit_clean:
                    amount, is_credit = debit_clean, False
                elif credit_clean:
                    amount, is_credit = credit_clean, True
                else:
                    continue  # no amount in either column — skip

                rows.append({
                    "date": date_str,
                    "description": desc,
                    "category_raw": category,
                    "amount": amount,
                    "is_credit": is_credit,
                })

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

    # Prefer the bank's own category column when available (PDF path),
    # fall back to keyword matching on description otherwise (CSV path).
    if "category_raw" in df.columns:
        df["category"] = df["category_raw"].str.lower().replace({
            "income": "income", "rent": "rent",
        })
        # Anything not cleanly mapped, re-derive from description as backup
        unmapped = ~df["category"].isin(list(CATEGORIES.keys()) + ["income"])
        df.loc[unmapped, "category"] = df.loc[unmapped, "description"].apply(categorize)
    else:
        df["category"] = df["description"].apply(categorize)

    df["amount"] = (df["amount"].astype(str).str.replace(",", "")
                     .apply(pd.to_numeric, errors="coerce").abs())

    df["date"] = pd.to_datetime(df["date"], format="%d-%b-%y", errors="coerce")

    n_bad_dates = df["date"].isna().sum()
    if n_bad_dates > 0:
        print(f"⚠️  {n_bad_dates} row(s) had unparseable dates and will be dropped:")
        print(df[df["date"].isna()][["description", "amount"]].to_string())

    n_before = len(df)
    df = df.dropna(subset=["amount", "date"])
    if len(df) < n_before:
        print(f"⚠️  Dropped {n_before - len(df)} row(s) total during cleaning.")

    df["weekday"] = df["date"].dt.day_name()
    df["month"]   = df["date"].dt.to_period("M").astype(str)
    return df