import os
from dotenv import load_dotenv

# Load .env if present (for local dev)
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "legal-doc-hackathon-2025")
LOCATION = os.getenv("LOCATION", "us-central1")
PROCESSOR_ID = os.getenv("PROCESSOR_ID", "fc048f040d3d92d0")
MODEL_ID = os.getenv("MODEL_ID", "gemini-1.5-pro")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
RAW_BUCKET = os.getenv("RAW_BUCKET", "raw")
