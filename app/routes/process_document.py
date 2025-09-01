from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
import uuid

router = APIRouter(tags=["document processing"])


class UploadResponse(BaseModel):
    file_id: str


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)):
    """
    Endpoint to upload a document (PDF or DOCX).
    Accepts a multipart file upload and returns a unique file ID.
    """
    # Generate a dummy file ID
    file_id = str(uuid.uuid4())
    return {"file_id": file_id}
