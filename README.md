
# ⚡ Multi-Provider FAQ Evaluation Engine

A proof-of-concept (PoC) application designed to benchmark **Claude**, **Gemini**, and **OpenAI** APIs. 
It checks for correctness, efficiency, and cost effectiveness of a model
---

## 🎯 Project Overview

When serving consumer support inquiries, LLMs must answer accurately while strictly avoiding hallucinations about business policies, pricing, and services. This sandbox executes identical consumer prompts across all three major AI providers alongside a baseline FAQ dataset to measure:

1. **Groundedness & Accuracy**: Does the model strictly stick to the FAQ context?
2. **Latency**: Which provider delivers the fastest Time-to-First-Byte (TTFB) and total execution time?
3. **Cost Efficiency**: Token consumption comparison per answer delivered.

---

## 🛠️ Tech Stack & Provider Models

|React (Vite/Tailwind CSS)| Frontend |
|FastAPI (Python)| Backend |
|Claude| `Claude-Haiku-3.5` |  `Claude-Haiku-4.5` |
|Gemini| `Gemini-3.7-Flash` | `Gemini 3.5 Flash-Lite`|
|ChatGPT| `GPT-5.6-Luna` | `GPT-4o-mini` |

---

### Prerequisites

* **Node.js**: v18.0.0+
* **Python** 3.10+ 
* Valid API Keys for Anthropic, Google Gemini, and OpenAI. (WIP)

### Installation

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/your-username/faq-llm-benchmark-poc.git](https://github.com/your-username/faq-llm-benchmark-poc.git)
   cd faq-llm-benchmark-poc
