# backend/tests/debug_pdf_parse.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.agents.statement_parser import parse_pdf_statement

path = "backend/data/test_perfect.pdf"   # change as needed
df = parse_pdf_statement(path)

print(f"Extracted {len(df)} rows")
print(df.head(10))
print("\nMissing/null amounts:", df["amount"].isna().sum() if "amount" in df else "no amount col")