# Legal Document AI - Backend

This repository contains the backend service for the Legal Document AI project. It is a FastAPI-based application designed to process, analyze, and manage legal documents.

## 📖 Overview

The backend serves as the core engine for the Legal Document AI platform. It provides a RESTful API for:

-   **Uploading Documents**: Accepts legal documents in PDF or DOCX format.
-   **Analyzing Content**: Extracts key information, identifies clauses, and will eventually provide AI-driven insights (summaries, pros/cons, loopholes).
-   **Retrieving Data**: Allows clients to fetch document status and analysis results.

The project is currently in a prototype stage, with stubbed data and responses to facilitate frontend development and future integration with Google Cloud AI services.

## ✨ Features

-   **FastAPI Framework**: Modern, fast (high-performance) web framework for building APIs with Python.
-   **OpenAPI Documentation**: Automatic interactive API documentation (via Swagger UI and ReDoc).
-   **Pydantic Data Validation**: Type hints and validation for robust request/response models.
-   **Modular Structure**: Code is organized by feature (routes, core logic) for scalability.
-   **In-Memory Database**: Dummy database for prototyping without requiring a persistent data store.
-   **Google Cloud Ready**: Designed for easy integration with services like Vertex AI, Document AI, and Cloud Run.

## 🚀 Getting Started

Follow these instructions to set up and run the project on your local machine.

### Prerequisites

-   Python 3.10+
-   `pip` and `venv`

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd legal-document-ai-backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Start the development server:**
    ```bash
    uvicorn app.main:app --reload
    ```

2.  **Access the API:**
    -   The API will be available at `http://127.0.0.1:8000`.
    -   Interactive API documentation (Swagger UI) can be accessed at `http://127.0.0.1:8000/docs`.

## ⚙️ API Endpoints

The following endpoints are available:

| Method | Path                       | Description                                                                 |
| :----- | :------------------------- | :-------------------------------------------------------------------------- |
| `GET`  | `/health`                  | Health check endpoint to verify if the service is running.                  |
| `POST` | `/process-document`        | Upload a document (PDF/DOCX) for processing.                                |
| `GET`  | `/documents`               | Get a list of all documents with their IDs and statuses.                    |
| `GET`  | `/documents/{doc_id}`      | Fetch the status and extracted text for a specific document.                |
| `POST` | `/analyze`                 | Request an analysis of a document, returning a summary, pros, cons, etc.    |

### Example Usage (cURL)

**1. Process a document:**
```bash
curl -X POST -F "file=@/path/to/your/document.pdf" http://127.0.0.1:8000/process-document
```
*Response:*
```json
{
  "doc_id": "dummy_doc_id",
  "message": "Document processing started."
}
```

**2. Get document status:**
```bash
curl -X GET http://127.0.0.1:8000/documents/doc123
```
*Response:*
```json
{
  "doc_id": "doc123",
  "status": "processed",
  "extracted_text": "Sample extracted text from the document."
}
```

**3. Analyze a document:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"file_id": "file123"}' http://127.0.0.1:8000/analyze
```
*Response:*
```json
{
  "summary": "This is a summary of the document.",
  "pros": ["Clear terms and conditions", "Well-defined responsibilities"],
  "cons": ["Complex language", "Ambiguous timelines"],
  "loopholes": ["No penalty for non-compliance"]
}
```

## 📁 Project Structure

```
.
├── app/
│   ├── core/
│   │   └── config.py        # Configuration settings
│   ├── routes/              # API route definitions
│   │   ├── analyze.py
│   │   ├── documents.py
│   │   ├── health.py
│   │   └── process_document.py
│   └── main.py              # FastAPI app entry point
├── tests/                   # Test suite
├── pyproject.toml           # Project configuration (e.g., for Black)
├── requirements.txt         # Python dependencies
└── README.md
```

## 🗺️ Roadmap

The following features are planned for future development:

-   [ ] **Integrate Google Document AI**: For robust text extraction from PDF and DOCX files.
-   [ ] **Connect to Gemini (Vertex AI)**: For AI-driven summarization, pro/con analysis, and loophole detection.
-   [ ] **Implement Persistent Storage**: Replace the in-memory database with a proper database solution (e.g., PostgreSQL).
-   [ ] **Authentication & Authorization**: Secure the API endpoints.
-   [ ] **Deploy to Cloud Run**: Set up CI/CD for automated deployment, logging, and monitoring.
