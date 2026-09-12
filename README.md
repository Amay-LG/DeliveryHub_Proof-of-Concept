# Gemini FAQ Assistant

A customer support tool that answers consumer inquiries by grounding **Google Gemini** responses in a structured FAQ knowledge base — no hallucinated policies, pricing, or service details.

---

## Project Overview

When serving consumer support inquiries, LLMs need to answer accurately while strictly avoiding hallucinations about business policies, pricing, and services. This app stores a curated set of FAQs in a PostgreSQL knowledge base, retrieves the most relevant entries for each incoming customer question, and passes them to Gemini as grounding context so responses stay accurate and on-policy.

**Core flow:**
1. A customer submits a question through the frontend.
2. The backend retrieves relevant FAQ entries from the PostgreSQL knowledge base.
3. Gemini generates a response grounded in those retrieved FAQs.
4. The answer is returned to the customer, staying consistent with your documented policies.

---

## Features

- **Grounded answers** — responses are constrained to the FAQ knowledge base rather than the model's general knowledge, and the model is instructed to say so explicitly when it has to fall back to its own knowledge.
- **Simple knowledge base management** — FAQs live in a PostgreSQL table (`faqs`) with `question` and `answer` columns, initialized and seeded via `k_base.py`.
- **Keyword-based retrieval** — relevant FAQs are pulled with a SQL `ILIKE` match against the customer's message (no vector database needed at this scale).
- **Message classification** — alongside the grounded answer, each response is classified into a category (`question`, `statement`, `greeting`, `request`) with a confidence score.
- **Lightweight stack** — FastAPI backend, React frontend.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/classify-message` | GET | Main endpoint. Takes `model_name` and `prompt` query params, retrieves relevant FAQs, and returns a grounded answer plus a message category and confidence score. |
| `/generate-message` | GET | Takes `model_name` and `prompt` query params and returns a raw Gemini response, with no FAQ grounding. |
| `/test-models` | GET | Diagnostic endpoint that sends the same prompt to `gemini-3.5-flash-lite` and `gemini-3.6-flash` in parallel and returns both responses with latency, for quick model comparisons. |

---

## Tech Stack

| Layer      | Technology                  |
|------------|------------------------------|
| Frontend   | React (Vite / Tailwind CSS)  |
| Backend    | FastAPI (Python)             |
| Database   | PostgreSQL                   |
| LLM        | Google Gemini API            |

---

## Prerequisites

- **Node.js**: v18.0.0+
- **Python**: 3.10+
- **PostgreSQL**: 16.15+
    - A valid **Database URL**
- A valid **Google Gemini API key**

---

## How to Set Up

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```

2. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   DATABASE_URL=postgresql://username:password@host:port/database_name
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize and seed the knowledge base**
   ```bash
   cd backend
   python k_base.py
   ```
   This creates the `faqs` table if it doesn't already exist and seeds it with your starting FAQ entries.

5. **Install frontend dependencies**
   ```bash
   cd ../frontend
   npm install
   ```

6. **Run the backend**
   ```bash
   cd ../backend
   uvicorn main:app --reload
   ```

7. **Run the frontend**
   ```bash
   cd ../frontend
   npm run dev
   ```
   Note: the backend's CORS settings currently only allow requests from `http://localhost:5173` (Vite's default dev port). Update the `allow_origins` list in `main.py` if your frontend runs elsewhere.

8. Open the app in your browser and start asking questions — answers will be grounded in the FAQs stored in your knowledge base.

---

## Updating the Knowledge Base

Add or edit entries directly in `k_base.py`'s seed list, or insert rows into the `faqs` table (e.g. via pgAdmin or `psql`) with a `question` and `answer` for each new FAQ.