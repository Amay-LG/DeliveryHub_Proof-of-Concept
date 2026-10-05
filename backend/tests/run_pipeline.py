"""
Step 2: Run all synthetic queries through the /generate-message endpoint.

Reads tests/synthetic_queries.json, hits the /generate-message endpoint
for each query, and saves the full results to tests/pipeline_results.json.

Each result includes the original query data plus the bot's actual response.
"""

import os
import json
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

QUERIES_PATH = os.path.join(os.path.dirname(__file__), "synthetic_queries.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "pipeline_results.json")

# Backend URL — when running tests from the host against Docker
BACKEND_URL = os.getenv("TEST_BACKEND_URL", "http://localhost:8000")
MODEL_NAME = "gemini-3.5-flash-lite"


def run_pipeline():
    with open(QUERIES_PATH) as f:
        queries = json.load(f)

    print(f"🔄 Running {len(queries)} queries through /generate-message...")
    print(f"   Backend: {BACKEND_URL}")
    print(f"   Model:   {MODEL_NAME}")
    print()

    results = []
    passed_count = 0
    error_count = 0

    for i, q in enumerate(queries):
        prompt = q["query"]

        # Retry logic for transient failures (rate limiting, etc.)
        max_retries = 2
        result = None
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                response = httpx.get(
                    f"{BACKEND_URL}/generate-message",
                    params={"model_name": MODEL_NAME, "prompt": prompt},
                    timeout=30.0,
                )
                elapsed = time.time() - start_time
                data = response.json()

                # Check if the backend returned a Gemini API error
                if data.get("error") and attempt < max_retries:
                    wait = 2 ** (attempt + 1)  # 2s, 4s backoff
                    print(f"    ⏳ Rate limited, retrying in {wait}s (attempt {attempt+1})...")
                    time.sleep(wait)
                    continue

                result = {
                    **q,
                    "bot_response": data.get("data", ""),
                    "http_status": data.get("status", response.status_code),
                    "latency_seconds": round(data.get("latency_seconds", elapsed), 2),
                    "error": data.get("data") if data.get("error") else None,
                }
                break

            except Exception as e:
                if attempt < max_retries:
                    wait = 2 ** (attempt + 1)
                    print(f"    ⏳ Error, retrying in {wait}s (attempt {attempt+1})...")
                    time.sleep(wait)
                    continue
                result = {
                    **q,
                    "bot_response": "",
                    "http_status": 0,
                    "latency_seconds": 0,
                    "error": str(e),
                }
                break

        if result.get("error"):
            status_icon = "💥"
            error_count += 1
        else:
            status_icon = "✅"
            passed_count += 1

        results.append(result)
        source = q["source_faq"]
        print(f"  {status_icon} [{i+1:3d}/{len(queries)}] ({source:14s}) {prompt[:60]}...")

        # Delay between requests to avoid rate limiting
        time.sleep(1.0)

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print()
    print(f"✅ Pipeline complete: {len(results)} queries processed")
    print(f"   Responses received: {passed_count}")
    print(f"   Errors:             {error_count}")
    print(f"   Saved to: {RESULTS_PATH}")
    return results


if __name__ == "__main__":
    run_pipeline()
