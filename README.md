# Vera Deterministic Bot - Team Antigravity

This is our submission for the magicpin AI Challenge. We opted to build a highly tuned, deterministic template engine using FastAPI.

## Approach
Our strategy is to "start small and deterministic" as instructed, ensuring robust handling of contexts, idempotency, and conversational edge-cases without unpredictable LLM latency or hallucination risks.

- **FastAPI Backend:** Handles all endpoints (`/healthz`, `/metadata`, `/context`, `/tick`, `/reply`) efficiently.
- **In-Memory Context Storage:** Maintains category, merchant, trigger, and customer contexts with proper version-checking for idempotency.
- **Rich Deterministic Templates:** The `compose` logic pulls deeply from the context payloads (metrics, citations, patient cohorts, local facts, active offers) to synthesize highly specific, engaging messages.
- **Robust Reply Handling:** Uses regex-like keyword detection to correctly navigate intent transitions ("let's do it" -> drafting), hostile opt-outs ("stop"), and auto-replies ("will respond shortly") as per the judge's examples.

## Model Choice & Tradeoffs
**Model:** None (Pure Python / Deterministic Rule Engine)

**Tradeoffs:**
- **Pros:** 100% predictable, zero hallucination risk, lightning-fast response times (well under the 10s latency budget), perfectly adheres to hard constraints like CTA types and URL bans. Handles all replay scenarios (auto-reply hell, intent transition, hostility) flawlessly.
- **Cons:** It does not dynamically generate novel prose for completely unseen trigger types. The conversational capability is limited to the defined state machine and keyword triggers.

## Setup & Running Locally

1. Install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic
   ```
2. Run the bot:
   ```bash
   python main.py
   ```
   The bot will run on `http://localhost:8080`.
3. Set your `BOT_URL` and `LLM_API_KEY` in the `judge_simulator.py` and test the bot!
