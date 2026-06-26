# backend/rag/tests/run_full_pipeline.py
"""
Full end-to-end pipeline test — run together with Sruthi.
Usage: python -m backend.rag.tests.run_full_pipeline
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from backend.agents.orchestrator import run_finsight_pipeline

SAMPLE_CSV = os.path.join(
    os.path.dirname(__file__),
    "../sample_pdfs/sample_statement.csv"
)
PDF_FOLDER = os.path.join(os.path.dirname(__file__), "../sample_pdfs")


def test_file(path: str, label: str):

    print("\n" + "=" * 70)
    print(f"FULL PIPELINE TEST: {label}")
    print("=" * 70)

    start = time.time()

    try:
        result = run_finsight_pipeline(path)

        elapsed = time.time() - start

        print(f"✓ Pipeline completed in {elapsed:.1f}s\n")

        print("--- PATTERNS ---")
        print(f"Total spent: ₹{result['patterns']['total_spent']:,.0f}")
        print(f"Top category: {result['patterns']['top_category']}")

        print("\n--- HEALTH SCORE ---")
        print(
            f"Score: {result['health_score']['score']}/100 "
            f"({result['health_score']['label']})"
        )

        # ==========================================================
        # ADVICE
        # ==========================================================

        print("\n--- ADVICE ---")

        advice = result["advice"]

        if isinstance(advice, list):
            advice = "\n".join(
                item.get("text", "")
                if isinstance(item, dict)
                else str(item)
                for item in advice
    )

        elif isinstance(advice, dict):
            advice = advice.get("text", "")

        print(advice[:300])

        if len(advice) > 300:
            print("...")

        empty_advice = not advice.strip()

        print(
            f"\n{'✗ ADVICE LOOKS EMPTY/BROKEN' if empty_advice else '✓ Advice generated'}"
            )

        # ==========================================================
        # SCHEMES
        # ==========================================================
        print("\n--- SCHEMES ---")

        schemes = result["schemes"]

        if isinstance(schemes, list):
            schemes = "\n".join(
                item.get("text", "")
                if isinstance(item, dict)
                else str(item)
                for item in schemes
    )

        elif isinstance(schemes, dict):
            schemes = schemes.get("text", "")

        print(schemes[:300])

        if len(schemes) > 300:
            print("...")

        empty_schemes = not schemes.strip()

        print(
            f"\n{'✗ SCHEMES LOOK EMPTY/BROKEN' if empty_schemes else '✓ Schemes generated'}"
            )
        # ==========================================================

        print("\n--- SAVINGS OPPORTUNITIES ---")
        print(f"Found: {len(result['savings_opportunities'])}")

        return {
            "label": label,
            "status": "success",
            "time": elapsed,
            "advice_ok": not empty_advice,
            "schemes_ok": not empty_schemes,
        }

    except Exception as e:

        print(f"PIPELINE FAILED: {e}")

        import traceback

        traceback.print_exc()

        return {
            "label": label,
            "status": "failed",
            "error": str(e),
        }


def run_all():

    results = []

    if os.path.exists(SAMPLE_CSV):
        results.append(test_file(SAMPLE_CSV, "Sample CSV"))
    else:
        print(f"⚠ Sample CSV not found at {SAMPLE_CSV}")

    if os.path.exists(PDF_FOLDER):
        pdfs = [f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf")]

        for pdf in pdfs:
            results.append(
                test_file(
                    os.path.join(PDF_FOLDER, pdf),
                    f"Real PDF: {pdf}",
                )
            )

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    for r in results:

        if r["status"] == "success":

            issues = []

            if not r["advice_ok"]:
                issues.append("advice empty")

            if not r["schemes_ok"]:
                issues.append("schemes empty")

            flag = "✓" if not issues else f"⚠ ({', '.join(issues)})"

            print(f"{flag} {r['label']} — {r['time']:.1f}s")

        else:

            print(f"✗ {r['label']} — FAILED: {r['error']}")

    print("=" * 70)


if __name__ == "__main__":
    run_all()