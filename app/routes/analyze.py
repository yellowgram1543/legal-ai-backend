from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Any, Dict

import json
import os
import re
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

from app.core.config import PROJECT_ID, LOCATION, MODEL_ID, GEMINI_KEY

router = APIRouter(tags=["analysis"]) 


class AnalyzeInput(BaseModel):
    file_id: str


class AnalyzeOutput(BaseModel):
    summary: str
    pros: List[str]
    cons: List[str]
    loopholes: List[str]


def _get_access_token() -> str:
    """Obtain an OAuth2 access token using the GEMINI_KEY service account JSON."""
    if not GEMINI_KEY or not os.path.exists(GEMINI_KEY):
        raise RuntimeError("GEMINI_KEY not configured or file not found")
    creds = service_account.Credentials.from_service_account_file(
        GEMINI_KEY, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(Request())
    return creds.token


def _extract_json(text: str) -> Dict[str, Any]:
    """Try to parse JSON from a model text. Attempts direct parse, fenced blocks, and braces extraction."""
    if not text:
        return {}

    # Direct attempt
    try:
        return json.loads(text)
    except Exception:
        pass

    # Look for fenced code blocks ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence_match:
        fenced = fence_match.group(1).strip()
        try:
            return json.loads(fenced)
        except Exception:
            pass

    # Extract first {...} block heuristically (handles nested braces poorly but works often)
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        candidate = text[brace_start: brace_end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return {}


def _coerce_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce parsed data into the required schema with defaults and type conversions."""
    def to_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]
        # If it's a string with bullets or commas, split
        if isinstance(value, str):
            # split on newlines or commas or semicolons
            parts = re.split(r"[\n,;]+", value)
            return [p.strip(" -•\t").strip() for p in parts if p.strip()]
        # Fallback single item list
        return [str(value)]

    summary = data.get("summary")
    if not isinstance(summary, str):
        # Try to synthesize a summary from any available field
        if isinstance(summary, (list, dict)):
            summary = json.dumps(summary)[:500]
        else:
            summary = ""

    result = {
        "summary": summary.strip(),
        "pros": to_list(data.get("pros")),
        "cons": to_list(data.get("cons")),
        "loopholes": to_list(data.get("loopholes")),
    }

    # Ensure keys exist
    for k in ("summary", "pros", "cons", "loopholes"):
        result.setdefault(k, [] if k != "summary" else "")
    return result


def analyze_text(text: str) -> Dict[str, Any]:
    """
    Use Vertex AI Gemini to analyze the input text and return a structured dict
    with keys: summary, pros, cons, loopholes. Ensures valid JSON output.
    """
    if not text or not text.strip():
        return {"summary": "", "pros": [], "cons": [], "loopholes": []}

    token = _get_access_token()
    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
        f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:generateContent"
    )

    system_prompt = (
        "You are a legal document analysis assistant. Analyze the user's document and respond strictly in JSON. "
        "JSON schema: {\"summary\": string, \"pros\": string[], \"cons\": string[], \"loopholes\": string[]}. "
        "Do not include any extra commentary or code fences."
    )

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": system_prompt + "\n\nDocument:\n" + text[:20000]}]},
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json"
        }
    }

    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as e:
        # On API failure, return empty structured response
        return {"summary": "", "pros": [], "cons": [], "loopholes": []}

    data = resp.json()

    # Vertex response can have candidates[0].content.parts[0].text or promptFeedback
    text_out = None
    try:
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text_out = parts[0].get("text")
        if not text_out:
            # Some versions use output[0].content[0].text
            outputs = data.get("output") or []
            if outputs and isinstance(outputs, list):
                text_out = outputs[0]
    except Exception:
        text_out = None

    parsed = _extract_json(text_out or "")
    coerced = _coerce_analysis(parsed)
    return coerced


# Attempt to import an external document retrieval function if present
try:
    # e.g., from app.services.documents import get_document_text
    from app.services.documents import get_document_text  # type: ignore
except Exception:
    # Fallback local stub for development/testing
    def get_document_text(file_id: str) -> str:
        if file_id == "123abc":
            return "This is a sample legal agreement between two parties covering terms, obligations, and liabilities."
        raise LookupError("Document not found")


@router.post("/analyze", response_model=AnalyzeOutput)
def analyze_document(input: AnalyzeInput):
    """
    Analyzes a previously uploaded document.

    - **file_id**: The unique identifier of the file to analyze.

    Returns a structured analysis of the document, including a summary,
    a list of pros, a list of cons, and any identified loopholes.
    """
    try:
        text = get_document_text(input.file_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="File not there.")
    except Exception as e:
        # Unexpected backend error
        raise HTTPException(status_code=500, detail=f"Failed to read document: {e}")

    try:
        result = analyze_text(text)
    except Exception as e:
        # If analysis fails, return a structured empty response rather than 500
        result = {"summary": "", "pros": [], "cons": [], "loopholes": []}

    return result
