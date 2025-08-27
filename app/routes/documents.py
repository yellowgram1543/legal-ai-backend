from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["documents"])


class ProcessedDocument(BaseModel):
    doc_id: str
    status: str
    extracted_text: Optional[str]


class DocumentMetadata(BaseModel):
    doc_id: str
    status: str


# Dummy in-memory "database" for processed documents
documents_db = {
    "doc123": {
        "doc_id": "doc123",
        "status": "processed",
        "extracted_text": "Sample extracted text from the document.",
    },
    "doc456": {"doc_id": "doc456", "status": "processing", "extracted_text": None},
}


@router.get("/documents/{doc_id}", response_model=ProcessedDocument)
def get_document(doc_id: str):
    """
    Endpoint to fetch the processed results of a specific document.
    Returns the document's status and the extracted text.
    """
    # Lookup the document in the dummy database
    document = documents_db.get(doc_id, None)
    if document:
        return document
    return {"doc_id": doc_id, "status": "not_found", "extracted_text": None}


@router.get("/documents", response_model=List[DocumentMetadata])
def list_documents():
    """
    Endpoint to list all processed documents with basic metadata.
    """
    # Extract metadata from the dummy database
    metadata_list = [
        {"doc_id": doc["doc_id"], "status": doc["status"]} for doc in documents_db.values()
    ]
    return metadata_list
