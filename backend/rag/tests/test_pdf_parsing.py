# backend/rag/tests/test_pdf_parsing.py
"""
Run this to test PDF statement parsing against real bank PDFs.
Place test PDFs in backend/rag/sample_pdfs/ first.
Usage: python -m backend.rag.tests.test_pdf_parsing
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.agents.statement_parser import parse_statement, parse_pdf_statement

PDF_FOLDER = os.path.join(os.path.dirname(__file__), "../sample_pdfs")

def test_single_pdf(path: str):
    filename = os.path.basename(path)
    print(f"\n{'─'*70}")
    print(f"Testing: {filename}")
    print("─" * 70)

    try:
        df = parse_statement(path)
        print(f"✓ Parsed successfully")
        print(f"  Transactions found: {len(df)}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Total amount: ₹{df['amount'].sum():,.2f}")
        print(f"  Categories detected: {df['category'].nunique()}")

        null_dates  = df["date"].isna().sum()
        null_amounts = df["amount"].isna().sum()
        if null_dates > 0:
            print(f"  ⚠️  {null_dates} rows have unparseable dates")
        if null_amounts > 0:
            print(f"  ⚠️  {null_amounts} rows have unparseable amounts")

        print(f"\n  Sample rows:")
        print(df[["date", "description", "amount", "category"]].head(3).to_string(index=False))

        return {"file": filename, "status": "success", "rows": len(df),
                "issues": null_dates + null_amounts}

    except Exception as e:
        print(f"✗ FAILED: {str(e)}")
        return {"file": filename, "status": "failed", "error": str(e)}

def run_pdf_tests():
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)
        print(f"Created {PDF_FOLDER} — add test bank statement PDFs here and re-run.")
        return []

    pdfs = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]
    if not pdfs:
        print(f"No PDFs found in {PDF_FOLDER}. Add 2-3 real bank statements and re-run.")
        return []

    print("=" * 70)
    print(f"PDF PARSING TEST — {len(pdfs)} files found")
    print("=" * 70)

    results = [test_single_pdf(os.path.join(PDF_FOLDER, pdf)) for pdf in pdfs]

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for r in results:
        if r["status"] == "success":
            flag = "✓" if r["issues"] == 0 else "⚠️"
            print(f"{flag} {r['file']}: {r['rows']} rows, {r['issues']} issues")
        else:
            print(f"✗ {r['file']}: FAILED — {r['error']}")
            print(f"   → Flag this format for Sruthi to fix the regex in statement_parser.py")

    return results

if __name__ == "__main__":
    run_pdf_tests()