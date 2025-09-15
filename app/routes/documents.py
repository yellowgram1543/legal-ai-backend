from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from google.cloud import storage
from google.oauth2 import service_account
import os
import sys
import json

from app.core.config import RAW_BUCKET, DOC_AI_KEY, PROJECT_ID

router = APIRouter(prefix="/documents", tags=["documents"])

# --- Pydantic Models ---
class DocumentStatus(BaseModel):
    doc_id: str
    status: str
    raw_filename: Optional[str] = None

class DocumentResult(BaseModel):
    doc_id: str
    status: str
    analysis: Dict[str, Any]

# --- Helper Functions ---
def _init_storage_client() -> storage.Client:
    creds = service_account.Credentials.from_service_account_file(DOC_AI_KEY)
    return storage.Client(project=PROJECT_ID, credentials=creds)

# --- API Endpoints ---
@router.get("", response_model=List[DocumentStatus])
def list_all_documents():
    """
    Lists all documents and their current status by scanning GCS buckets.
    This simulates a database query.
    """
    try:
        storage_client = _init_storage_client()
        bucket = storage_client.bucket(RAW_BUCKET)

        raw_blobs = {os.path.splitext(os.path.basename(b.name))[0] for b in bucket.list_blobs(prefix="raw/")}
        processed_blobs = {os.path.splitext(os.path.basename(b.name))[0] for b in bucket.list_blobs(prefix="processed/")}

        all_docs = []
        all_doc_ids = raw_blobs.union(processed_blobs)

        for doc_id in all_doc_ids:
            if not doc_id: continue
            status = "processed" if doc_id in processed_blobs else "processing"
            # Find the original raw filename
            raw_filename = next((b.name for b in bucket.list_blobs(prefix=f"raw/{doc_id}")), None)
            all_docs.append(DocumentStatus(doc_id=doc_id, status=status, raw_filename=raw_filename))
        
        return all_docs
    except Exception as e:
        print(f"[ERROR] Failed to list documents: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Failed to retrieve document list.")

@router.get("/{file_id}")
def get_document_details(file_id: str):
    """
    Retrieves the status or the full analysis of a specific document.
    """
    try:
        storage_client = _init_storage_client()
        bucket = storage_client.bucket(RAW_BUCKET)
        
        doc_id, _ = os.path.splitext(file_id)
        processed_blob_name = f"processed/{doc_id}.json"
        processed_blob = bucket.blob(processed_blob_name)

        if processed_blob.exists():
            print(f"[INFO] Found processed analysis for {doc_id}", file=sys.stderr)
            analysis_data = json.loads(processed_blob.download_as_string())
            return DocumentResult(doc_id=doc_id, status="processed", analysis=analysis_data)
        
        # Check if the raw file exists to determine if it's still processing
        raw_blobs = list(bucket.list_blobs(prefix=f"raw/{doc_id}"))
        if raw_blobs:
            return {"doc_id": doc_id, "status": "processing", "detail": "Analysis is not yet available."}
        
        raise HTTPException(status_code=404, detail="Document not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to retrieve document {file_id}: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document details.")

@router.delete("/{file_id}")
def delete_document_data(file_id: str, background_tasks: BackgroundTasks):
    """
    Deletes a document's raw file and its processed analysis from GCS.
    """
    doc_id, _ = os.path.splitext(file_id)
    print(f"[INFO] Initiating deletion for doc_id: {doc_id}", file=sys.stderr)

    def delete_in_background(doc_id_to_delete):
        try:
            storage_client = _init_storage_client()
            bucket = storage_client.bucket(RAW_BUCKET)

            # Delete raw file(s)
            raw_blobs_to_delete = list(bucket.list_blobs(prefix=f"raw/{doc_id_to_delete}"))
            if raw_blobs_to_delete:
                for blob in raw_blobs_to_delete:
                    blob.delete()
                    print(f"[OK] Deleted raw file: {blob.name}", file=sys.stderr)
            
            # Delete processed file
            processed_blob_name = f"processed/{doc_id_to_delete}.json"
            processed_blob = bucket.blob(processed_blob_name)
            if processed_blob.exists():
                processed_blob.delete()
                print(f"[OK] Deleted processed file: {processed_blob.name}", file=sys.stderr)
            
            # Placeholder for DB deletion
            print(f"[INFO] DB: Deleting records for doc_id '{doc_id_to_delete}'.", file=sys.stderr)

        except Exception as e:
            print(f"[ERROR] Background deletion for {doc_id_to_delete} failed: {e}", file=sys.stderr)

    background_tasks.add_task(delete_in_background, doc_id)
    
    return {"message": f"Deletion process for document {doc_id} has been initiated."}
