from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id SERIAL PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def seed_faqs():
    # Replace these with your actual questions and answers
    faqs = [
        (0, "How long does delivery take from USA to India?", "Fast delivery takes 3–5 days, Normal delivery takes 7–10 days, Air Cargo takes around 20 days, and Sea Cargo can take up to 3–4 months."),
        (1, "Which courier does DeliveryHub use?", "DeliveryHub currently uses FedEx for reliable international delivery from USA to India."),
        (2, "How is the shipping cost calculated?", "Shipping cost is calculated based on the delivery type, route, and service selected. The price and delivery time are shown instantly before confirmation."),
    ]
 
    conn = get_connection()
    cur = conn.cursor()
 
    # Only seed if the table is currently empty, so this stays safe to run every time
    cur.execute("SELECT COUNT(*) FROM faqs")
    count = cur.fetchone()[0]
 
    if count == 0:
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO faqs (question, answer) VALUES %s",
            faqs
        )
        conn.commit()
        print(f"Seeded {len(faqs)} FAQs.")
    else:
        print("faqs table already has data, skipping seed.")
 
    cur.close()
    conn.close()

init_db()