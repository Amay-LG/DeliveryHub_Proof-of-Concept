from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras
import httpx
# pyrefly: ignore [missing-import]
from pgvector.psycopg2 import register_vector

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")



def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            embedded VECTOR(3072)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

from functools import lru_cache

@lru_cache(maxsize=512)
def _cached_embedding(text: str) -> tuple:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {
            "parts": [{"text": text}]
        }
    }
    
    response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    return tuple(data["embedding"]["values"])

def get_embedding(text: str) -> list[float]:
    normalized = " ".join(text.strip().lower().split())
    return list(_cached_embedding(normalized))

def seed_faqs():
    # Replace these with actual questions and answers
    faqs = [
        ("How long does delivery take from USA to India?", "Fast delivery takes 3–5 days, Normal delivery takes 7–10 days, Air Cargo takes around 20 days, and Sea Cargo can take up to 3–4 months."),
        ("Which courier does DeliveryHub use?", "DeliveryHub currently uses FedEx for reliable international delivery from USA to India."),
        ("How is the shipping cost calculated?", "Shipping cost is calculated based on the delivery type, route, and service selected. The price and delivery time are shown instantly before confirmation."),
    ]
 
    conn = get_connection()
    register_vector(conn)
    cur = conn.cursor()
 
    # Only seed if the table is currently empty
    cur.execute("SELECT COUNT(*) FROM faqs")
    count = cur.fetchone()[0]
 
    if count == 0:
        faq_records = []
        for q, a in faqs:
            # Create embedding based on both question and answer
            text_to_embed = f"Question: {q}\nAnswer: {a}"
            emb = get_embedding(text_to_embed)
            faq_records.append((q, a, emb))

        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO faqs (question, answer, embedded) VALUES %s",
            faq_records
        )
        conn.commit()
        print(f"Seeded {len(faqs)} FAQs.")
    else:
        print("faqs table already has data, skipping seed.")
 
    cur.close()
    conn.close()
