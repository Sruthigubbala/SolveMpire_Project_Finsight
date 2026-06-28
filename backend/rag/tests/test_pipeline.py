# backend/tests/test_pipeline.py
import sys, os, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.agents.orchestrator import run_finsight_pipeline

def run_test(file_path: str, label: str):
    print(f"\n{'='*60}")
    print(f"TESTING: {label}  ({file_path})")
    print(f"{'='*60}")

    start = time.time()
    try:
        result = run_finsight_pipeline(file_path)
    except Exception as e:
        print(f"❌ PIPELINE CRASHED: {e}")
        import traceback
        traceback.print_exc()
        return None
    elapsed = time.time() - start

    # Sanity checks on every key
    required_keys = ["df", "patterns", "advice", "schemes",
                      "savings_opportunities", "health_score"]
    for k in required_keys:
        status = "✓" if k in result else "✗ MISSING"
        print(f"  {status} {k}")

    print(f"\n  Rows parsed:        {len(result['df'])}")
    print(f"  Total spent:        ₹{result['patterns']['total_spent']:,.0f}")
    print(f"  Top category:       {result['patterns']['top_category']}")
    print(f"  Health score:       {result['health_score']['score']}/100")
    print(f"  Savings opps found: {len(result['savings_opportunities'])}")
    print(f"  Advice length:      {len(result['advice'])} chars")
    print(f"  Schemes length:     {len(result['schemes'])} chars")
    print(f"  Pipeline time:      {elapsed:.1f}s")

    return result

if __name__ == "__main__":
    run_test("backend/data/sample_statements.csv", "Sample CSV")
    run_test("backend/data/sample_statements.csv", "Sample CSV")

    # Add real bank statements here as you collect them this week
    # run_test("backend/data/test_real_1.csv", "Real Bank Statement 1")
    # run_test("backend/data/test_real_2.pdf", "Real Bank Statement 2 (PDF)")