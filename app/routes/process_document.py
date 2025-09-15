from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel
from google.cloud import storage
from google.oauth2 import service_account
from app.core.config import RAW_BUCKET, DOC_AI_KEY, PROJECT_ID
import uuid
import os
import sys

# Import the new background task orchestrator
from app.routes.analyze import trigger_analysis

router = APIRouter(tags=["document processing"])


class UploadResponse(BaseModel):
    doc_id: str
    status: str


@router.post("/upload", response_model=UploadResponse)
def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a document to Google Cloud Storage and trigger the analysis background task.
    - Generates a unique doc_id (UUID4).
    - Uploads to bucket RAW_BUCKET under prefix raw/.
    - Adds a background task to start the analysis workflow.
    - Returns JSON with doc_id and initial status="processing" immediately.
    """
    try:
        if file is None or file.filename is None:
            raise HTTPException(status_code=400, detail="No file provided")

        _, ext = os.path.splitext(file.filename)
        doc_id = str(uuid.uuid4())
        doc_id_with_ext = f"{doc_id}{ext}"
        blob_name = f"raw/{doc_id_with_ext}"
        content_type = file.content_type or "application/octet-stream"

        print(f"[INFO] Uploading file to GCS: {blob_name}", file=sys.stderr)

        content = file.file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Initialize storage client
        try:
            if DOC_AI_KEY and os.path.exists(DOC_AI_KEY):
                creds = service_account.Credentials.from_service_account_file(DOC_AI_KEY)
                client = storage.Client(project=PROJECT_ID, credentials=creds)
            else:
                client = storage.Client(project=PROJECT_ID)
        except Exception as auth_err:
            print(f"[ERROR] GCS Auth failed: {auth_err}", file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Auth setup failed: {auth_err}")

        bucket = client.bucket(RAW_BUCKET)
        blob = bucket.blob(blob_name)

        blob.upload_from_string(content, content_type=content_type)
        print(f"[OK] File uploaded successfully.", file=sys.stderr)

        # Add the analysis workflow as a background task
        background_tasks.add_task(trigger_analysis, doc_id_with_ext, content_type)
        print(f"[INFO] Added background analysis task for doc_id: {doc_id}", file=sys.stderr)

        # Return the base doc_id without extension for consistency
        return UploadResponse(doc_id=doc_id, status="processing")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to upload file: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
