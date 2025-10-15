# Chatbot Backend

This Flask backend exposes REST endpoints for chat and sessions and integrates with Google Generative AI (Gemini).

Quick start:
1) Create env file
   cp .env.example .env
   # Edit .env to set GEMINI_API_KEY (required), optionally GEMINI_MODEL.

2) Install and run:
   python -m pip install -r requirements.txt
   python -m flask --app run.py run --port 3001

Minimal chat test:
   curl -s -X POST http://localhost:3001/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"Say hello in one short sentence."}'

Expected 200:
   {"reply":"Hello! Great to meet you!"}

Environment variables:
- GEMINI_API_KEY (required)
- GEMINI_MODEL (optional) If unset, backend defaults to gemini-2.5-flash. The value is honored verbatim; no silent fallback is applied. Example: gemini-2.5-flash.
- CORS_ALLOWED_ORIGINS (optional; default *)
- DATABASE_URL (optional; falls back to local SQLite)
