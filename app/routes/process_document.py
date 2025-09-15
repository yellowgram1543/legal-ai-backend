from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from google.cloud import storage
from google.oauth2 import service_account
from app.core.config import RAW_BUCKET, DOC_AI_KEY, PROJECT_ID
import uuid
import os

router = APIRouter(tags=["document processing"])


class UploadResponse(BaseModel):
    doc_id: str
    status: str


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to Google Cloud Storage raw bucket.
    - Generates a unique doc_id (UUID4)
    - Keeps original extension (.pdf/.docx)
    - Uploads to bucket RAW_BUCKET under prefix raw/
    - Returns JSON with doc_id and initial status="processing"
    """
    try:
        if file is None or file.filename is None:
            raise HTTPException(status_code=400, detail="No file provided")

        # Generate UUID doc_id
        doc_id = str(uuid.uuid4())

        # Derive original extension (including the dot). If none, keep empty string.
        _, ext = os.path.splitext(file.filename)
        ext = (ext or "").lower()

        # Build GCS blob path: raw/{doc_id}{ext}
        blob_name = f"raw/{doc_id}{ext}"

        # Read bytes from the uploaded file (sync context)
        # UploadFile.file is a SpooledTemporaryFile; use .read() directly
        content = file.file.read()
        if content is None or len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Initialize storage client using DOC_AI_KEY credentials if provided
        try:
            if DOC_AI_KEY and os.path.exists(DOC_AI_KEY):
                creds = service_account.Credentials.from_service_account_file(DOC_AI_KEY)
                client = storage.Client(project=PROJECT_ID, credentials=creds)
            else:
                client = storage.Client(project=PROJECT_ID)
        except Exception as auth_err:
            raise HTTPException(status_code=500, detail=f"Auth setup failed: {auth_err}")

        bucket = client.bucket(RAW_BUCKET)
        blob = bucket.blob(blob_name)

        # Try to guess content type from the uploaded file
        content_type = file.content_type or "application/octet-stream"

        # Upload from memory
        blob.upload_from_string(content, content_type=content_type)

        return {"doc_id": doc_id, "status": "processing"}
    except HTTPException:
        # re-raise expected HTTP errors
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
