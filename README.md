# gemini-chatbot-platform-149385-149394

## Backend quick start

1) Copy env example and set your Gemini API key:
   cp chatbot_backend/.env.example chatbot_backend/.env
   # Then edit chatbot_backend/.env and set GEMINI_API_KEY

2) Run the Flask backend (port may vary depending on environment):
   python -m pip install -r chatbot_backend/requirements.txt
   python -m flask --app chatbot_backend/run.py run --port 3001

3) Test minimal chat endpoint:
   curl -s -X POST http://localhost:3001/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"Say hello in one short sentence."}'

Expected 200 response:
   {"reply":"Hello! Great to meet you!"}

Environment variables of interest:
- GEMINI_API_KEY (required)
- GEMINI_MODEL (optional) If unset, defaults to gemini-1.5-flash. If set to an unsupported model (e.g., a newer version not available in the current SDK), the backend will attempt to use it and gracefully fall back to a supported model to avoid 502s. Supported shortlist: gemini-1.5-flash, gemini-1.5-flash-8b, gemini-1.5-pro.
- CORS_ALLOWED_ORIGINS (optional; default *)
- DATABASE_URL (optional; falls back to local SQLite)