"""
Step 3: LLM Judge — evaluate each chatbot response for correctness.

Reads tests/pipeline_results.json, uses Gemini as a judge to grade each
response, and saves the final test report to tests/test_report.json.

Judging criteria:
  1. FACTUAL ACCURACY — Does the response contain the expected key facts?
  2. FAQ GROUNDING  — If should_cite_faq=true, does it use FAQ info (not hallucinate)?
  3. OFF-TOPIC HANDLING — For off-topic queries, does the bot correctly indicate
     it doesn't have specific FAQ info rather than making things up?

Verdict: PASS or FAIL with a brief reason.
"""

import os
import json
import time
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

RESULTS_PATH = os.path.join(os.path.dirname(__file__), "pipeline_results.json")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "test_report.json")

# How many results to batch into a single judge call (keeps prompts manageable)
BATCH_SIZE = 10


def build_judge_prompt(batch):
    """Build the LLM judge prompt for a batch of results."""
    items_text = ""
    for i, r in enumerate(batch):
        items_text += f"""
--- Test Case {i+1} ---
User Query: {r['query']}
Source FAQ: {r['source_faq']}
Expected Facts: {json.dumps(r['expected_facts'])}
Should Cite FAQ: {r['should_cite_faq']}
Bot Response: {r['bot_response']}
Error: {r.get('error', None)}
"""

    prompt = f"""You are a strict QA judge evaluating a delivery-company chatbot's responses.
The chatbot is called DeliveryHub and uses the /generate-message endpoint (raw Gemini output).

For EACH test case below, evaluate:
1. FACTUAL ACCURACY: Does the bot's response contain the expected facts? Check each expected fact.
2. FAQ GROUNDING: If should_cite_faq is true, does the response ground its answer in known FAQ data 
   (not hallucinate new information)?
3. OFF-TOPIC HANDLING: If source_faq is "off_topic", does the bot correctly indicate it cannot 
   answer from the FAQ, rather than making up an answer?
4. CATEGORY: Is the classification category reasonable for the user's query?

For each test case, output a JSON object with:
- "index": the test case number (1-based within this batch)
- "verdict": "PASS" or "FAIL"
- "reason": a brief explanation (1-2 sentences)
- "facts_found": list of expected facts that WERE found in the response
- "facts_missing": list of expected facts that were NOT found in the response

Return ONLY a JSON array of objects. No markdown fences, no extra text.

{items_text}"""

    return prompt


def judge_batch(batch, api_key):
    """Send a batch of results to the LLM judge and return verdicts."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": build_judge_prompt(batch)}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0,  # Deterministic judging
        },
    }

    response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()

    result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    verdicts = json.loads(result_text)
    return verdicts


def rule_based_checks(result):
    """Fast rule-based checks that don't need an LLM."""
    issues = []

    # Check for HTTP/API errors
    if result.get("error"):
        issues.append(f"API error: {result['error']}")

    # Check response is not empty
    if not result.get("bot_response", "").strip():
        issues.append("Empty bot response")

    # Check latency (flag if > 15 seconds)
    if result.get("latency_seconds", 0) > 15:
        issues.append(f"High latency: {result['latency_seconds']}s")

    return issues


def run_judge():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")

    with open(RESULTS_PATH) as f:
        results = json.load(f)

    print(f"🔄 Judging {len(results)} chatbot responses...")
    print()

    all_verdicts = []

    # First pass: rule-based checks
    for i, r in enumerate(results):
        rule_issues = rule_based_checks(r)
        if rule_issues:
            all_verdicts.append({
                "index": i,
                "query": r["query"],
                "source_faq": r["source_faq"],
                "bot_response": r["bot_response"],
                "verdict": "FAIL",
                "reason": "Rule check failed: " + "; ".join(rule_issues),
                "facts_found": [],
                "facts_missing": r.get("expected_facts", []),
                "judge": "rule_based",
            })
        else:
            all_verdicts.append(None)  # Placeholder — will be filled by LLM judge

    # Second pass: LLM judge on results that passed rule checks
    llm_indices = [i for i, v in enumerate(all_verdicts) if v is None]
    llm_results = [results[i] for i in llm_indices]

    if llm_results:
        for batch_start in range(0, len(llm_results), BATCH_SIZE):
            batch = llm_results[batch_start:batch_start + BATCH_SIZE]
            batch_indices = llm_indices[batch_start:batch_start + BATCH_SIZE]

            print(f"  Judging batch {batch_start // BATCH_SIZE + 1} "
                  f"({len(batch)} items)...")

            try:
                verdicts = judge_batch(batch, api_key)

                for j, verdict in enumerate(verdicts):
                    idx = batch_indices[j]
                    r = results[idx]
                    all_verdicts[idx] = {
                        "index": idx,
                        "query": r["query"],
                        "source_faq": r["source_faq"],
                        "bot_response": r["bot_response"],
                        "verdict": verdict.get("verdict", "FAIL"),
                        "reason": verdict.get("reason", "No reason provided"),
                        "facts_found": verdict.get("facts_found", []),
                        "facts_missing": verdict.get("facts_missing", []),
                        "judge": "llm",
                    }
            except Exception as e:
                for j in range(len(batch)):
                    idx = batch_indices[j]
                    r = results[idx]
                    all_verdicts[idx] = {
                        "index": idx,
                        "query": r["query"],
                        "source_faq": r["source_faq"],
                        "bot_response": r["bot_response"],
                        "verdict": "FAIL",
                        "reason": f"Judge error: {str(e)}",
                        "facts_found": [],
                        "facts_missing": r.get("expected_facts", []),
                        "judge": "error",
                    }

            time.sleep(1.0)  # Rate limit courtesy

    # Build report
    passed = [v for v in all_verdicts if v and v["verdict"] == "PASS"]
    failed = [v for v in all_verdicts if v and v["verdict"] == "FAIL"]

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_queries": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "pass_rate": f"{len(passed) / len(results) * 100:.1f}%",
        "summary_by_faq": {},
        "failures": failed,
        "all_verdicts": all_verdicts,
    }

    # Summary by FAQ source
    for faq_id in ["courier", "cost", "delivery_time", "off_topic"]:
        faq_verdicts = [v for v in all_verdicts if v and v["source_faq"] == faq_id]
        faq_passed = [v for v in faq_verdicts if v["verdict"] == "PASS"]
        report["summary_by_faq"][faq_id] = {
            "total": len(faq_verdicts),
            "passed": len(faq_passed),
            "failed": len(faq_verdicts) - len(faq_passed),
            "pass_rate": f"{len(faq_passed) / max(len(faq_verdicts), 1) * 100:.1f}%",
        }

    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print()
    print("=" * 60)
    print(f"  TEST REPORT — {report['timestamp']}")
    print("=" * 60)
    print(f"  Total:      {report['total_queries']}")
    print(f"  ✅ Passed:   {report['passed']}")
    print(f"  ❌ Failed:   {report['failed']}")
    print(f"  Pass Rate:  {report['pass_rate']}")
    print()
    print("  By FAQ:")
    for faq_id, stats in report["summary_by_faq"].items():
        print(f"    {faq_id:16s}  {stats['passed']}/{stats['total']}  ({stats['pass_rate']})")
    print()

    if failed:
        print("=" * 60)
        print("  FAILURES (inspect these manually):")
        print("=" * 60)
        for f_item in failed:
            print(f"\n  ❌ [{f_item['index']}] ({f_item['source_faq']})")
            print(f"     Query:    {f_item['query']}")
            print(f"     Response: {f_item['bot_response'][:120]}...")
            print(f"     Reason:   {f_item['reason']}")
            if f_item.get("facts_missing"):
                print(f"     Missing:  {f_item['facts_missing']}")
    print()
    print(f"  Full report saved to: {REPORT_PATH}")

    return report


if __name__ == "__main__":
    run_judge()
