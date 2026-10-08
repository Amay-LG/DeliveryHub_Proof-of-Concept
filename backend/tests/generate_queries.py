
# Step 1: Generate 80–100 synthetic test queries from the raw FAQ documents.

# Uses the Gemini API to produce questions, then saves them to tests/synthetic_queries.json.

# Each generated query includes:
#   - query:           The user message to send to the chatbot
#   - source_faq:      Which FAQ it relates to ("courier", "cost", "delivery_time", or "off_topic")
#   - expected_facts:  Key facts the response MUST contain to be correct
#   - should_cite_faq: Whether the bot should ground its answer in the FAQ


import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

# ── Raw FAQ Documents ────────────────────────────────────────────────
RAW_FAQS = [
    {
        "id": "courier",
        "question": "Which courier does DeliveryHub use?",
        "answer": "DeliveryHub currently uses FedEx for reliable international delivery from USA to India.",
        "key_facts": ["FedEx", "USA to India"]
    },
    {
        "id": "cost",
        "question": "How is the shipping cost calculated?",
        "answer": "Shipping cost is calculated based on the delivery type, route, and service selected. The price and delivery time are shown instantly before confirmation.",
        "key_facts": ["delivery type", "route", "service", "price shown before confirmation"]
    },
    {
        "id": "delivery_time",
        "question": "How long does delivery take from USA to India?",
        "answer": "Fast delivery takes 3–5 days, Normal delivery takes 7–10 days, Air Cargo takes around 20 days, and Sea Cargo can take up to 3–4 months.",
        "key_facts": ["3–5 days", "7–10 days", "20 days", "3–4 months"]
    },
]

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "synthetic_queries.json")

GENERATION_PROMPT = """You are a test-data generator for a delivery-company chatbot called DeliveryHub.

Below are the 3 FAQ documents the chatbot has access to:

FAQ 1 – Courier:
Q: Which courier does DeliveryHub use?
A: DeliveryHub currently uses FedEx for reliable international delivery from USA to India.

FAQ 2 – Cost:
Q: How is the shipping cost calculated?
A: Shipping cost is calculated based on the delivery type, route, and service selected. The price and delivery time are shown instantly before confirmation.

FAQ 3 – Delivery Time:
Q: How long does delivery take from USA to India?
A: Fast delivery takes 3–5 days, Normal delivery takes 7–10 days, Air Cargo takes around 20 days, and Sea Cargo can take up to 3–4 months.

Generate exactly 90 synthetic user queries that a real customer might type into the chatbot.
Distribute them as follows:

• 25 queries about the COURIER (FAQ 1) — variations like typos, slang, indirect phrasing, 
  multi-part questions, different languages (transliterated), politeness levels, etc.
• 25 queries about the COST (FAQ 2) — same variety.
• 25 queries about the DELIVERY TIME (FAQ 3) — same variety.
• 15 OFF-TOPIC queries that the chatbot should NOT be able to answer from the FAQ —
  e.g., "Can I return a package?", "Do you ship to Europe?", "What's the weather?",
  greetings like "hi", nonsense strings, etc.

For each query, output a JSON object with these fields:
{
  "query": "<the user message>",
  "source_faq": "<courier | cost | delivery_time | off_topic>",
  "expected_facts": ["<fact1>", "<fact2>", ...],
  "should_cite_faq": true/false
}

For courier queries, expected_facts should include things like "FedEx", "USA to India".
For cost queries, expected_facts should include things like "delivery type", "route", "service", "price shown before confirmation".
For delivery_time queries, expected_facts should include relevant time values like "3-5 days", "7-10 days", "20 days", "3-4 months".
For off-topic queries:
- expected_facts should list what the bot should say (e.g., ["not in FAQ", "cannot answer"] or relevant keywords)
- should_cite_faq should be false

Return ONLY a JSON array of 90 objects. No markdown fences, no commentary."""


def generate_synthetic_queries():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": GENERATION_PROMPT}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 1.0,   # High creativity for diverse phrasings
        },
    }

    print("🔄 Generating synthetic test queries with Gemini...")
    response = httpx.post(url, headers=headers, json=payload, timeout=60.0)
    response.raise_for_status()

    result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    queries = json.loads(result_text)

    # Validate structure
    assert isinstance(queries, list), f"Expected list, got {type(queries)}"
    for i, q in enumerate(queries):
        assert "query" in q, f"Query {i} missing 'query' field"
        assert "source_faq" in q, f"Query {i} missing 'source_faq' field"
        assert "expected_facts" in q, f"Query {i} missing 'expected_facts' field"
        assert "should_cite_faq" in q, f"Query {i} missing 'should_cite_faq' field"

    # Save to disk
    with open(OUTPUT_PATH, "w") as f:
        json.dump(queries, f, indent=2)

    # Print distribution summary
    dist = {}
    for q in queries:
        dist[q["source_faq"]] = dist.get(q["source_faq"], 0) + 1

    print(f"✅ Generated {len(queries)} synthetic queries")
    print(f"   Distribution: {json.dumps(dist, indent=2)}")
    print(f"   Saved to: {OUTPUT_PATH}")
    return queries


if __name__ == "__main__":
    generate_synthetic_queries()
