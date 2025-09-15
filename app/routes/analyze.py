from typing import Any, Dict, List
import json
import os
import re
import sys
import requests
from google.cloud import documentai, storage
from google.oauth2 import service_account
from google.auth.transport.requests import Request

from app.core.config import (
    PROJECT_ID, LOCATION, MODEL_ID, GEMINI_KEY, RAW_BUCKET, PROCESSOR_ID, DOC_AI_KEY
)

# --- 1. AUTHENTICATION AND CONFIGURATION ---
def _get_access_token() -> str:
    """Obtain an OAuth2 access token for Vertex AI."""
    creds = service_account.Credentials.from_service_account_file(
        GEMINI_KEY, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds.token

def _init_storage_client() -> storage.Client:
    """Initialize a GCS storage client."""
    creds = service_account.Credentials.from_service_account_file(DOC_AI_KEY)
    return storage.Client(project=PROJECT_ID, credentials=creds)

def _init_docai_client() -> documentai.DocumentProcessorServiceClient:
    """Initialize the Document AI client."""
    opts = {"api_endpoint": f"{LOCATION}-documentai.googleapis.com"}
    creds = service_account.Credentials.from_service_account_file(DOC_AI_KEY)
    return documentai.DocumentProcessorServiceClient(client_options=opts, credentials=creds)

# --- 2. DOCUMENT AI TEXT EXTRACTION ---
def extract_text_with_docai(bucket: str, file_name: str, mime_type: str) -> str:
    """Process a document with Document AI to extract text."""
    print(f"[INFO] Starting Document AI processing for gs://{bucket}/{file_name}", file=sys.stderr)
    docai_client = _init_docai_client()

    resource_name = docai_client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    gcs_document = documentai.GcsDocument(gcs_uri=f"gs://{bucket}/{file_name}", mime_type=mime_type)
    request = documentai.ProcessRequest(
        name=resource_name,
        gcs_document=gcs_document,
        skip_human_review=True
    )

    try:
        result = docai_client.process_document(request=request)
        print("[OK] Document AI processing successful.", file=sys.stderr)
        return result.document.text
    except Exception as e:
        print(f"[ERROR] Document AI processing failed: {e}", file=sys.stderr)
        raise RuntimeError(f"Failed to process document with Document AI: {e}")

# --- 3. GEMINI ANALYSIS ---
def analyze_text(text: str) -> Dict[str, Any]:
    """Use Vertex AI Gemini to analyze text and return structured JSON."""
    # This function remains largely the same as before, focusing on analysis
    if not text or not text.strip():
        return {"summary": "Document is empty.", "pros": [], "cons": [], "loopholes": []}

    token = _get_access_token()
    url = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:generateContent"
    
    system_prompt = (
        "You are a legal document analysis assistant. Analyze the user's document and respond strictly in JSON. "
        "The JSON schema must be: {\"summary\": string, \"pros\": string[], \"cons\": string[], \"loopholes\": string[]}. "
        "Do not include any extra commentary, explanations, or markdown fences. Just the JSON object."
    )

    payload = {
        "contents": [{"role": "user", "parts": [{"text": system_prompt + "\n\nDocument:\n" + text[:25000]}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096, "responseMimeType": "application/json"}
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        response_data = resp.json()
        text_out = response_data["candidates"][0]["content"]["parts"][0]["text"]
        # The response should be clean JSON due to responseMimeType, but we can still parse it robustly
        return json.loads(text_out)
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"[ERROR] Gemini analysis or parsing failed: {e}", file=sys.stderr)
        return {"summary": "Failed to analyze document.", "pros": [], "cons": [], "loopholes": []}

# --- 4. SAVE AND UPDATE STATUS ---
def _save_analysis_to_gcs(storage_client: storage.Client, doc_id: str, analysis_data: Dict[str, Any]):
    """Save the structured analysis JSON to the processed/ bucket."""
    bucket = storage_client.bucket(RAW_BUCKET)
    blob_name = f"processed/{doc_id}.json"
    blob = bucket.blob(blob_name)
    
    try:
        blob.upload_from_string(
            data=json.dumps(analysis_data, indent=2),
            content_type="application/json"
        )
        print(f"[OK] Analysis saved to gs://{RAW_BUCKET}/{blob_name}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Failed to save analysis to GCS: {e}", file=sys.stderr)

def _update_status_in_db(doc_id: str, status: str):
    """
    Placeholder function to update the document status in a database.
    Replace this with your actual database logic (e.g., SQL, NoSQL).
    """
    print(f"[INFO] DB: Updating status for doc_id '{doc_id}' to '{status}'.", file=sys.stderr)
    # Example database logic:
    # with get_db_connection() as conn:
    #     cursor = conn.cursor()
    #     cursor.execute("UPDATE documents SET status = %s WHERE id = %s", (status, doc_id))
    #     conn.commit()
    pass

# --- 5. MAIN BACKGROUND TASK ORCHESTRATOR ---
def trigger_analysis(doc_id_with_ext: str, mime_type: str):
    """
    The main background task to orchestrate the analysis workflow.
    1. Extracts text using Document AI.
    2. Analyzes text with Gemini.
    3. Saves the result to GCS.
    4. Updates the status in the database.
    """
    doc_id, _ = os.path.splitext(doc_id_with_ext)
    raw_file_name = f"raw/{doc_id_with_ext}"
    print(f"--- Starting background analysis for doc_id: {doc_id} ---", file=sys.stderr)

    try:
        # Step 1: Extract text with Document AI
        _update_status_in_db(doc_id, "extracting_text")
        extracted_text = extract_text_with_docai(RAW_BUCKET, raw_file_name, mime_type)

        if not extracted_text:
            print("[WARN] Text extraction yielded no content. Aborting analysis.", file=sys.stderr)
            _update_status_in_db(doc_id, "error_empty_document")
            return

        # Step 2: Analyze text with Gemini
        _update_status_in_db(doc_id, "analyzing")
        analysis_result = analyze_text(extracted_text)

        # Step 3: Save the structured JSON output to GCS
        storage_client = _init_storage_client()
        _save_analysis_to_gcs(storage_client, doc_id, analysis_result)

        # Step 4: Update the document's status to 'processed'
        _update_status_in_db(doc_id, "processed")
        print(f"--- Background analysis for doc_id: {doc_id} complete. ---", file=sys.stderr)

    except Exception as e:
        print(f"[FATAL] An error occurred during the background analysis for {doc_id}: {e}", file=sys.stderr)
        _update_status_in_db(doc_id, "error_processing_failed")
