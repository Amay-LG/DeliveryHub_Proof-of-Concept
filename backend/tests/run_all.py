"""
run_all.py — Full end-to-end test pipeline orchestrator.

Runs all three steps in sequence:
  1. Generate synthetic queries (LLM → synthetic_queries.json)
  2. Run chatbot pipeline       (API → pipeline_results.json)
  3. Judge responses            (LLM + Rules → test_report.json)

Usage:
  python -m tests.run_all                  # Run everything
  python -m tests.run_all --skip-generate  # Reuse existing queries
  python -m tests.run_all --skip-pipeline  # Reuse existing responses (re-judge only)
"""

import sys
import time

def main():
    skip_generate = "--skip-generate" in sys.argv
    skip_pipeline = "--skip-pipeline" in sys.argv

    print("╔══════════════════════════════════════════════════════════╗")
    print("║       DeliveryHub Chatbot — Test Pipeline               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # ── Step 1: Generate synthetic queries ────────────────────────
    if not skip_generate:
        print("━" * 60)
        print("  STEP 1 / 3 — Generate Synthetic Test Queries")
        print("━" * 60)
        from tests.generate_queries import generate_synthetic_queries
        queries = generate_synthetic_queries()
        print()
        time.sleep(1)
    else:
        print("  ⏭  Skipping query generation (--skip-generate)")
        print()

    # ── Step 2: Run chatbot pipeline ──────────────────────────────
    if not skip_pipeline:
        print("━" * 60)
        print("  STEP 2 / 3 — Run Chatbot Pipeline")
        print("━" * 60)
        from tests.run_pipeline import run_pipeline
        results = run_pipeline()
        print()
        time.sleep(1)
    else:
        print("  ⏭  Skipping pipeline run (--skip-pipeline)")
        print()

    # ── Step 3: Judge responses ───────────────────────────────────
    print("━" * 60)
    print("  STEP 3 / 3 — LLM Judge + Rule Checks")
    print("━" * 60)
    from tests.judge_responses import run_judge
    report = run_judge()

    # ── Final summary ─────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                    PIPELINE COMPLETE                    ║")
    print("╠══════════════════════════════════════════════════════════╣")
    n_failed = report["failed"]
    if n_failed == 0:
        print("║  🎉 All tests passed! No failures to inspect.          ║")
    else:
        print(f"║  👀 {n_failed:3d} failure(s) need human inspection.            ║")
        print("║     → Open tests/test_report.json → check 'failures'   ║")
    print("╚══════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
