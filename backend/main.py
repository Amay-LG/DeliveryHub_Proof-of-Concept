import os
import httpx
import asyncio
import json
import psycopg2
import psycopg2.extras
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


@app.get("/classify-message")
async def classify_message(model_name, prompt):
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
                    "You are a message classifier. Classify the user's message into exactly one "
                    "of these categories: question, statement, greeting, request. "
                    "Also give your confidence in that classification, from 0 to 1."
                    "Use the FAQ entries below as your "
                    "primary source of truth if they're relevant. If none of them answer the "
                    "question, say so and answer from your own knowledge, making clear that "
                    "it isn't from the FAQ.\n\nFAQ entries:\n" + faq_context 
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
                        "enum": ["question", "statement", "greeting", "request"]
                    },
                    "confidence": {"type": "NUMBER"},
                    "response": {"type": "STRING"}
                },
                "required": ["category", "confidence", "response"]
            }
        }
    }

    timeout_settings = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout_settings) as client:
        response = await client.post(url, headers=headers, json=payload)

    result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    classification=json.loads(result_text)

    return {
        "status": response.status_code,
        "category": classification["category"],
        "confidence": classification["confidence"],
        "response": classification["response"]
    }

# @app.get("/test-models")
# async def evaluate_gemini_models():
#     api_key = os.getenv("GEMINI_API_KEY")
#     if not api_key:
#         return {"error": "API key is missing"}

#     url1 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
#     url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
#     headers = {"Content-Type": "application/json"}
#     payload = {
#         "contents": [{"parts": [{"text": "Hello! Please reply with your best joke."}]}]
#     }

#     timeout_settings = httpx.Timeout(30.0)
    
#     async with httpx.AsyncClient(timeout=timeout_settings) as client:
#         task1 = client.post(url1, headers=headers, json=payload)
#         task2 = client.post(url2, headers=headers, json=payload)
        
#         response1, response2 = await asyncio.gather(task1, task2)
        
#     return {
#         "model_3_5_lite": {
#             "status": response1.status_code, 
#             "latency_seconds": response1.elapsed.total_seconds(), # Extracts the exact time
#             "data": response1.json()["candidates"][0]["content"]["parts"][0]["text"]
#         },
#         "model_3_6_flash": {
#             "status": response2.status_code, 
#             "latency_seconds": response2.elapsed.total_seconds(), # Extracts the exact time
#             "data": response2.json()["candidates"][0]["content"]["parts"][0]["text"]
#         }
#     }

@app.get("/generate-message")
async def get_message_from_gemini(model_name, prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "API key is missing"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    timeout_settings = httpx.Timeout(30.0)
    
    async with httpx.AsyncClient(timeout=timeout_settings) as client:
        response = await client.post(url, headers=headers, json=payload)
        
    return {
        "status": response.status_code,
        "latency_seconds": response.elapsed.total_seconds(),
        "data": response.json()["candidates"][0]["content"]["parts"][0]["text"]
    }