import os
import httpx
import asyncio
import json
import psycopg2
import psycopg2.extras
from enum import Enum
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Import initialization functions from k_base.py
from k_base import init_db, seed_faqs

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when FastAPI starts up, before accepting incoming requests
    init_db()
    seed_faqs()
    yield
    # Code placed here runs on server shutdown (if needed)

app = FastAPI(lifespan=lifespan)
DATABASE_URL = os.getenv("DATABASE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# pyrefly: ignore [missing-import]
from pgvector.psycopg2 import register_vector

NUM_FAQS_TO_MATCH = 3

def get_relevant_faqs(prompt: str, limit: int = NUM_FAQS_TO_MATCH):
    try:
        from k_base import get_embedding
        emb = get_embedding(prompt)
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return []

    conn = psycopg2.connect(DATABASE_URL)
    register_vector(conn)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(
        "SELECT question, answer FROM faqs ORDER BY embedded <=> %s::vector LIMIT %s", 
        (emb, limit)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [{"question": r["question"], "answer": r["answer"]} for r in rows]


class PromptCategory(str, Enum):
    GET_A_QUOTE = "GET_A_QUOTE"
    QUESTION = "QUESTION"
    OTHER = "OTHER"

# Aliases for direct access
Category = PromptCategory
GET_A_QUOTE = PromptCategory.GET_A_QUOTE
QUESTION = PromptCategory.QUESTION
OTHER = PromptCategory.OTHER


async def get_a_quote(model, prompt):
    return {
        "status": 200,
        "response": "Thank you for requesting a quote! Instant online quote calculation is coming soon."
    }


async def classify_prompt(model, prompt) -> PromptCategory:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "API key is missing"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    valid_categories = [cat.value for cat in PromptCategory]

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are an intent classifier for DeliveryHub, an international parcel shipping service between the USA and India.\n"
                    "Classify the user's prompt into exactly one of the following categories:\n"
                    "- GET_A_QUOTE: The user is asking for a shipping quote, price estimate, or shipping rate calculation for sending packages/parcels.\n"
                    "- QUESTION: The user is asking a general question, inquiry, or FAQ regarding DeliveryHub's services, delivery times, couriers, or policies.\n"
                    "- OTHER: Any other message, greeting, chit-chat, unclear input, or off-topic request.\n\n"
                    f"Choose exactly one category from: {', '.join(valid_categories)}."
                )
            }]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "category": {
                        "type": "STRING",
                        "enum": valid_categories
                    }
                },
                "required": ["category"]
            }
        }
    }

    timeout_settings = httpx.Timeout(30.0)

    try:
        async with httpx.AsyncClient(timeout=timeout_settings) as client:
            response = await client.post(url, headers=headers, json=payload)

        response_data = response.json()
        if "candidates" in response_data and response_data["candidates"]:
            result_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            category_str = json.loads(result_text).get("category", "").strip().upper()
            return PromptCategory(category_str)
    except Exception as e:
        print(f"Error in classify_prompt: {e}")

    return PromptCategory.OTHER

@app.get("/question")
async def question(model_name, prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "API key is missing"}

    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    faqs = get_relevant_faqs(prompt)
    faq_context = "\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in faqs]) if faqs else "No relevant FAQ entries found."
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are the official customer service assistant for DeliveryHub, an international shipping service "
                    "specializing in parcel delivery between the USA and India.\n\n"
                    "Instructions:\n"
                    "1. Identity: Always speak as DeliveryHub. Assume all inquiries about shipping partners, rates, or delivery "
                    "times refer to DeliveryHub. Never state that you are an AI that cannot ship items or ask which company the user means.\n"
                    "2. Strict Grounding: Rely strictly on the FAQ entries provided below. Do not use outside knowledge or make up rates/timelines.\n"
                    "3. Out of Scope / Missing Information: If the question cannot be answered using the provided FAQ entries (e.g. customs duties, "
                    "jokes, order cancellation, mobile app, or off-topic queries), you MUST explicitly state that the answer is not in the FAQ and "
                    "that you cannot answer it, and direct them to support@deliveryhub.com.\n"
                    "4. Terse & Broad Inputs: If a user sends short queries (e.g. 'cost?', 'delivery time?', 'transport company name?'), do not ask "
                    "for order details or clarification. State the relevant policy directly from the FAQ.\n"
                    "FAQ entries:\n" + faq_context
                )
            }]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "response": {"type": "STRING"}
                },
                "required": ["response"]
            }
        }
    }

    timeout_settings = httpx.Timeout(30.0)
    
    async with httpx.AsyncClient(timeout=timeout_settings) as client:
        response = await client.post(url, headers=headers, json=payload)

    response_data = response.json()

    # Handle Gemini API errors (rate limiting, content filtering, etc.)
    if "candidates" not in response_data:
        error_msg = response_data.get("error", {}).get("message", "Unknown Gemini API error")
        return {
            "status": response.status_code,
            "latency_seconds": 0,
            "data": f"Gemini API error: {error_msg}",
            "error": True
        }
        
    raw_response = response_data["candidates"][0]["content"]["parts"][0]["text"]

    return {
        "status": response.status_code,
        "latency_seconds": response.elapsed.total_seconds(),
        "response": json.loads(raw_response)['response']
    }


@app.get("/respond_to_prompt")
@app.get("/respond-to-prompt")
async def respond_to_prompt(prompt: str):
    model = "gemini-3.5-flash-lite"
    category = await classify_prompt(model, prompt)

    handlers = {
        PromptCategory.GET_A_QUOTE: get_a_quote,
        PromptCategory.QUESTION: question,
        # Open to expanding later with additional customer request handlers
    }

    handler = handlers.get(category)
    if handler:
        if asyncio.iscoroutinefunction(handler):
            return await handler(model, prompt)
        else:
            return handler(model, prompt)

    return {
        "status": 200,
        "response": "I'm sorry, I didn't quite understand that. Please try again, or ask a question about our delivery services or request a shipping quote."
    }