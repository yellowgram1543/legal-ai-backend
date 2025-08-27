# Legal Document AI - Backend

This repository contains the backend service for the Legal Document AI project.

## Overview
The backend is built using **FastAPI** and serves as the core engine for processing legal documents. It handles:

- **Document Upload**: Accepts PDF/DOCX files for processing.
- **Document Analysis**: Extracts text, clauses, and key information from documents (currently stubbed for prototype; AI integration with Gemini/Vertex AI planned).
- **Document Retrieval**: Provides endpoints to fetch processed document results and metadata.
- **Health Monitoring**: A `/health` endpoint to verify service status.

## Features
- FastAPI-based API with OpenAPI/Swagger documentation.
- Pydantic models for request/response validation.
- Dummy in-memory database for prototyping and frontend integration.
- Modular and scalable structure for easy integration with Google Cloud services (Vertex AI, Document AI, Cloud Run).

## Tech Stack
- Python 3.10+
- FastAPI
- Uvicorn (ASGI server)
- Pydantic for data validation
- Google Cloud libraries (to be integrated)

## Project Status
- Skeleton and API contract implemented.
- Dummy responses in place for frontend and cloud integration.
- Ready for AI logic and GCP integration in subsequent phases.

## Next Steps
1. Integrate Document AI for text extraction.
2. Connect Gemini (Vertex AI) for AI-driven summarization, pros/cons, and loophole detection.
3. Refactor routes into modular structure if needed.
4. Deploy to Cloud Run and set up logging/monitoring.
