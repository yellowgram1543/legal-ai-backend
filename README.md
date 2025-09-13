# Legal Document AI - Backend

This repository contains the backend service for the Legal Document AI project.

## Overview
The backend is built with FastAPI and exposes HTTP endpoints to upload and analyze legal documents. 
It currently provides stubbed/prototype implementations and a simple health check. 
Planned integrations include Google Cloud Document AI for extraction and Vertex AI (Gemini) for analysis.

What it does now:
- Document Upload: Accepts PDF/DOCX via multipart form-data and returns a file_id.
- Document Analysis: Returns a dummy summary, pros/cons, and loopholes for a known file_id.
- Health Monitoring: `/health` endpoint to verify service status.

## Tech Stack
- Python 3.10+
- FastAPI
- Uvicorn (ASGI server)
- Pydantic v2 for data validation
- python-dotenv for local env loading
- Pytest for tests
- Google Cloud client libraries (present in requirements; integration TODO)

## Requirements
- Python 3.10 or newer
- Pip (or a virtual environment tool like venv/pyenv)
- (Optional) Google Cloud credentials if you work on GCP integration

## Setup
1. Clone the repository.
2. Create and activate a virtual environment.
   - Windows (PowerShell):
     - python -m venv .venv
     - .venv\\Scripts\\Activate.ps1
   - macOS/Linux:
     - python3 -m venv .venv
     - source .venv/bin/activate
3. Install dependencies:
   - pip install -r requirements.txt
4. (Optional) Create a .env file in the project root to set environment variables listed below.

## Running the server
- Development (auto-reload):
  - uvicorn app.main:app --reload
- Specify host/port (example):
  - uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
- Production (example; tune workers/timeouts as needed):
  - uvicorn app.main:app --host 0.0.0.0 --port 8000

Once running, visit:
- OpenAPI docs (Swagger UI): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Entry point
- ASGI app: app.main:app

## Available endpoints
- GET /health → {"status": "healthy"}
- POST /upload → accepts file in form field `file`, returns `{ "file_id": str }`
- POST /analyze → accepts JSON `{ "file_id": str }`, returns dummy analysis for a specific id

## Environment variables
Loaded via app/core/config.py (python-dotenv supports loading from a local .env file):
- PROJECT_ID: GCP project id (default: empty). TODO: used when integrating GCP.
- LOCATION: GCP region for services (default: us-central1).
- PROCESSOR_ID: Document AI processor id (default: empty). TODO.
- MODEL_ID: Vertex AI model id for analysis (default: gemini-1.5-pro). TODO.
- GOOGLE_APPLICATION_CREDENTIALS: Path to a GCP service account JSON key (default: empty). Required for local usage of GCP clients. TODO.

If you are not working on GCP features yet, you can leave these unset.

## Scripts
No project-specific run scripts are defined. Use uvicorn commands above.
- Formatter: black is configured via pyproject.toml (line length 100). Run manually if desired:
  - python -m pip install black
  - black .

## Testing
- Install dev deps (already included in requirements.txt): pytest, httpx, fastapi test client comes with FastAPI.
- Run tests:
  - pytest

There is a sample test at tests/test_health.py which exercises the /health endpoint.

## Project structure
- app/
  - main.py (FastAPI app and router includes)
  - core/
    - config.py (loads env vars; placeholders for GCP integration)
  - routes/
    - health.py (GET /health)
    - process_document.py (POST /upload)
    - analyze.py (POST /analyze)
- tests/
  - test_health.py
- requirements.txt (runtime and test dependencies)
- pyproject.toml (black formatter config)
- LICENSE (Apache 2.0)
- README.md (this file)

## Project status
- Skeleton and API contract implemented.
- Dummy responses for prototyping and frontend integration.
- Ready for AI logic and GCP integration in subsequent phases.

## Next steps / TODO
- Integrate Document AI for text extraction.
- Connect Vertex AI (Gemini) for summarization, pros/cons, and loophole detection.
- Add persistence/storage for uploaded files and results.
- Add authentication/authorization (if required).
- Add deployment configuration (e.g., Dockerfile, Cloud Run) and CI.

## License
Apache License 2.0. See LICENSE for details.
