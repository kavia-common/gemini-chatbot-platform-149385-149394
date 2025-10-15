# gemini-chatbot-platform-149385-149394

## Backend quick start

1) Copy env example and set your Gemini API key:
   cp chatbot_backend/.env.example chatbot_backend/.env
   # Then edit chatbot_backend/.env and set GEMINI_API_KEY

2) Run the Flask backend (port may vary depending on environment):
   python -m pip install -r chatbot_backend/requirements.txt
   # Recommended:
   python chatbot_backend/run.py
   # Or:
   python -m flask --app chatbot_backend/run.py run --host 0.0.0.0 --port 3001

Health check:
   curl -s http://localhost:3001/healthz

3) Test minimal chat endpoint:
   curl -s -X POST http://localhost:3001/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"Say hello in one short sentence."}'

Expected 200 response:
   {"reply":"Hello! Great to meet you!"}

Environment variables of interest:
- GEMINI_API_KEY (required)
- GEMINI_MODEL (optional) If unset, defaults to gemini-2.5-flash. The backend honors this value verbatim and does not silently fall back. Ensure your SDK/key has access to the specified model. Example: gemini-2.5-flash.
- CORS_ALLOWED_ORIGINS (optional; default *)
- DATABASE_URL (optional; falls back to local SQLite)