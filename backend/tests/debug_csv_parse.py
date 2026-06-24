# backend/tests/debug_csv_parse.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
from backend.agents.statement_parser import parse_statement, categorize

# ── Change this to whichever CSV you're testing ──────────────────────
path = "backend/data/test_real_1.csv"

print(f"{'='*60}")
print(f"DEBUG: CSV PARSE TEST")
print(f"File: {path}")
print(f"{'='*60}\n")

# ── Step 1: Check the raw file BEFORE parsing ─────────────────────────
# This catches header/encoding issues before they hide inside parse_statement()
try:
    raw = pd.read_csv(path)
    print("Raw columns found:", list(raw.columns))
    print("Raw row count:    ", len(raw))
    print("\nFirst 3 raw rows:")
    print(raw.head(3).to_string())
except Exception as e:
    print(f"❌ Could not even read raw CSV: {e}")
    sys.exit(1)

print(f"\n{'-'*60}\n")

# ── Step 2: Run it through the actual parser used by the pipeline ────
try:
    df = parse_statement(path)
except Exception as e:
    print(f"❌ parse_statement() CRASHED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"Parsed {len(df)} rows (after dropping invalid amounts)")
print(f"Columns after parsing: {list(df.columns)}\n")

print("First 10 parsed rows:")
print(df[["date", "description", "amount", "category", "weekday", "month"]].head(10).to_string())

# ── Step 3: Data quality checks ───────────────────────────────────────
print(f"\n{'-'*60}")
print("DATA QUALITY CHECKS")
print(f"{'-'*60}")

null_dates  = df["date"].isna().sum()
null_amts   = df["amount"].isna().sum()
zero_amts   = (df["amount"] == 0).sum()
uncategorized = (df["category"] == "other").sum()

print(f"Rows with null/unparseable date:  {null_dates}")
print(f"Rows with null amount:             {null_amts}  (already dropped if any)")
print(f"Rows with zero amount:             {zero_amts}")
print(f"Rows categorized as 'other':       {uncategorized} / {len(df)} "
      f"({uncategorized/len(df)*100:.0f}%)")

if uncategorized / len(df) > 0.3:
    print("\n⚠️  Over 30% of transactions fell into 'other'.")
    print("   These descriptions aren't matching any keyword in CATEGORIES — "
          "worth adding more keywords in statement_parser.py.")
    print("\n   Sample 'other' descriptions:")
    print(df[df["category"] == "other"]["description"].head(10).to_string(index=False))

# ── Step 4: Category breakdown preview ────────────────────────────────
print(f"\n{'-'*60}")
print("CATEGORY BREAKDOWN (debit-like rows only)")
print(f"{'-'*60}")
debits = df[~df["description"].str.lower().str.contains("credit|salary|stipend", na=False)]
print(debits.groupby("category")["amount"].sum().sort_values(ascending=False).to_string())

# ── Step 5: Test categorize() on individual strings ───────────────────
# Useful for quickly checking why a specific merchant isn't being caught
print(f"\n{'-'*60}")
print("SPOT-CHECK CATEGORIZE() ON SAMPLE DESCRIPTIONS")
print(f"{'-'*60}")
for desc in df["description"].head(5):
    print(f"  '{desc}'  →  {categorize(desc)}")

print(f"\n{'='*60}")
print("DONE")
print(f"{'='*60}")