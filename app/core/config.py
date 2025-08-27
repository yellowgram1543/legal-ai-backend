import os
from dotenv import load_dotenv

# Load .env if present (for local dev)
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "")
LOCATION = os.getenv("LOCATION", "us-central1")
PROCESSOR_ID = os.getenv("PROCESSOR_ID", "")
MODEL_ID = os.getenv("MODEL_ID", "gemini-1.5-pro")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
