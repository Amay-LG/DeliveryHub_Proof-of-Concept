import os
import httpx
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

@app.get("/evaluate-models")
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