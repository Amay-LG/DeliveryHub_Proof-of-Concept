import asyncio
import os
import httpx
from fastapi import FastAPI
from dotenv import load_dotenv
from google import genai

# Loads the variables from .env into your environment
load_dotenv()

app = FastAPI()

@app.get("/fetch-data")
async def fetch_external_data():
    # Retrieve the key securely
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return {"error": "API key is missing"}

    # Define the external API endpoint and authorization header
    url1 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
    url2 = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{
            "parts": [{"text": "Tell me a short joke about programming."}]
        }]
    }

    timeout_settings = httpx.Timeout(60.0)
    
    # Make an asynchronous API call
    async with httpx.AsyncClient(timeout=timeout_settings) as client:
        task1 = client.post(url1, headers=headers, json=payload)
        task2 = client.post(url2, headers=headers, json=payload)

        response1, response2 = await asyncio.gather(task1, task2)

        
    return {
        "3.5_Flash_Lite": {"status": response1.status_code, "latency_seconds": response1.elapsed.total_seconds(), "data": response1.json()["candidates"][0]["content"]["parts"][0]["text"]},
        "3.7_Flash": {"status": response2.status_code, "latency_seconds": response2.elapsed.total_seconds(), "data": response2.json()["candidates"][0]["content"]["parts"][0]["text"]}
    }