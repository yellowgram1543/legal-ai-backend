from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from google.cloud import storage
from app.core.config import RAW_BUCKET
import uuid

router = APIRouter(tags=["document processing"]) 


class UploadResponse(BaseModel):
    doc_id: str
    status: str


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to Google Cloud Storage raw bucket.
    - Generates a unique doc_id (UUID4)
    - Uploads the file content to GCS bucket named RAW_BUCKET with blob name = doc_id
    - Returns JSON with doc_id and initial status="processing"
    """
    try:
        if file is None or file.filename is None:
            raise HTTPException(status_code=400, detail="No file provided")

        # Generate UUID doc_id
        doc_id = str(uuid.uuid4())

        # Read bytes from the uploaded file (sync context)
        # UploadFile.file is a SpooledTemporaryFile; use .read() directly
        content = file.file.read()
        if content is None or len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Initialize storage client (uses GOOGLE_APPLICATION_CREDENTIALS or env-based auth)
        client = storage.Client()
        bucket = client.bucket(RAW_BUCKET)
        blob = bucket.blob(doc_id)

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
