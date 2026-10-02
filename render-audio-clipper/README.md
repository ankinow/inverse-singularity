# Render Audio Clipper (isolated deploy branch)

Reusable short-clip service for media analysis.

Endpoints:
- GET /health
- GET /probe?url=...
- GET /comments?url=...&comment_id=...
- GET /clip?url=...&start=0&duration=30&format=mp3

Limits are environment-controlled. Default source allowlist: YouTube only.
A header API key can be enabled with API_KEY after initial deployment tests.

Render native Python:
- Build: pip install -r render-audio-clipper/requirements.txt
- Start: uvicorn app:app --app-dir render-audio-clipper --host 0.0.0.0 --port $PORT
