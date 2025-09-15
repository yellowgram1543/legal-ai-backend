# -------------------------
import os
from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
PROCESSOR_ID = os.getenv("PROCESSOR_ID", "fc048f040d3d92d0")
DOC_AI_KEY = os.getenv("DOC_AI_KEY")        # path to docai/gcs key json
GEMINI_KEY = os.getenv("GEMINI_KEY")        # path to gemini key json
MODEL_ID = os.getenv("MODEL_ID", "gemini-2.5-pro")
RAW_BUCKET = os.getenv("RAW_BUCKET", "legal-ai-docs")