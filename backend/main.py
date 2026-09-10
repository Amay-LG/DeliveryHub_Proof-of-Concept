import os
import httpx
import asyncio
import json
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test-models")
async def evaluate_gemini_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "API key is missing"}

    url1 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": "Hello! Please reply with your best joke."}]}]
    }

    timeout_settings = httpx.Timeout(30.0)
    
    async with httpx.AsyncClient(timeout=timeout_settings) as client:
        task1 = client.post(url1, headers=headers, json=payload)
        task2 = client.post(url2, headers=headers, json=payload)
        
        response1, response2 = await asyncio.gather(task1, task2)
        
    return {
        "model_3_5_lite": {
            "status": response1.status_code, 
            "latency_seconds": response1.elapsed.total_seconds(), # Extracts the exact time
            "data": response1.json()["candidates"][0]["content"]["parts"][0]["text"]
        },
        "model_3_6_flash": {
            "status": response2.status_code, 
            "latency_seconds": response2.elapsed.total_seconds(), # Extracts the exact time
            "data": response2.json()["candidates"][0]["content"]["parts"][0]["text"]
        }
    }

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

@app.get("/classify-message")
async def classify_message(model_name, prompt):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "API key is missing"}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are a message classifier. Classify the user's message into exactly one "
                    "of these categories: question, statement, greeting, request. "
                    "Also give your confidence in that classification, from 0 to 1."
                    "Finally, respond to the message in a helpful and friendly manner, but do not include that response in your classification output."
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