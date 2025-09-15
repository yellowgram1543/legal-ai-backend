from typing import Optional
import io
import os

from google.cloud import storage
from google.oauth2 import service_account

from app.core.config import RAW_BUCKET, DOC_AI_KEY, PROJECT_ID

# Optional heavy libs are listed in requirements; import lazily where needed

def _init_storage_client() -> storage.Client:
    """Initialize a GCS storage client using service account if provided."""
    if DOC_AI_KEY and os.path.exists(DOC_AI_KEY):
        creds = service_account.Credentials.from_service_account_file(DOC_AI_KEY)
        return storage.Client(project=PROJECT_ID, credentials=creds)
    return storage.Client(project=PROJECT_ID)


def _find_blob_for_doc(bucket: storage.Bucket, file_id: str) -> Optional[storage.Blob]:
    """Find the first blob matching raw/{file_id} with any extension.
    Preference order: exact pdf, docx, txt, else first returned.
    """
    prefix = f"raw/{file_id}"
    blobs = list(bucket.list_blobs(prefix=prefix))
    if not blobs:
        return None

    # Prefer common types by extension
    priority_exts = [".pdf", ".docx", ".txt"]
    by_ext = {os.path.splitext(b.name)[1].lower(): b for b in blobs}
    for ext in priority_exts:
        if ext in by_ext and by_ext[ext].name.startswith(prefix):
            return by_ext[ext]

    # Fallback: the blob whose name starts exactly with prefix (in case multiple)
    for b in blobs:
        if b.name.startswith(prefix):
            return b
    return blobs[0]


def _extract_text_from_pdf(data: bytes) -> str:
    # Try pdfplumber first for better layout/text extraction
    try:
        import pdfplumber  # type: ignore
        text_parts = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts).strip()
    except Exception:
        pass

    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader  # type: ignore
        reader = PdfReader(io.BytesIO(data))
        text_parts = []
        for page in getattr(reader, "pages", []):
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t:
                text_parts.append(t)
        return "\n\n".join(text_parts).strip()
    except Exception:
        return ""


def _extract_text_from_docx(data: bytes) -> str:
    try:
        from docx import Document  # type: ignore
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text).strip()
    except Exception:
        return ""


def _extract_text_generic(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except Exception:
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""


def get_document_text(file_id: str) -> str:
    """Load the uploaded document from GCS using the doc_id returned by /upload and return plain text.

    Looks for a blob under raw/{file_id} with any extension. Supports PDF, DOCX, and TXT.
    Raises LookupError if the file cannot be found.
    """
    if not file_id or not isinstance(file_id, str):
        raise LookupError("Invalid file id")

    try:
        client = _init_storage_client()
    except Exception as e:
        # Surface auth issues as generic failure during analysis
        raise RuntimeError(f"GCS auth failed: {e}")

    bucket = client.bucket(RAW_BUCKET)

    blob = _find_blob_for_doc(bucket, file_id)
    if not blob:
        raise LookupError("Document not found")

    try:
        data = blob.download_as_bytes()
    except Exception as e:
        raise RuntimeError(f"Failed to download document: {e}")

    ext = os.path.splitext(blob.name)[1].lower()
    text = ""

    if ext == ".pdf":
        text = _extract_text_from_pdf(data)
    elif ext == ".docx":
        text = _extract_text_from_docx(data)
    elif ext in (".txt", ".text"):
        text = _extract_text_generic(data)
    else:
        # Best effort for unknown types
        text = _extract_text_generic(data)

    return (text or "").strip()
