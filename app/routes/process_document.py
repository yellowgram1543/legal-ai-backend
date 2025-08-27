from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

router = APIRouter(tags=["document processing"])


class ProcessDocumentResponse(BaseModel):
    doc_id: str
    message: str


@router.post("/process-document", response_model=ProcessDocumentResponse)
def process_document(file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF document and process it.
    Currently stubbed to only return a dummy response.
    """
    # For now, return a dummy response
    return {"doc_id": "dummy_doc_id", "message": "Document processing started."}
