import os
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

def test_gemini_api():
    # Load service account key from GEMINI_KEY env
    key_path = os.getenv("GEMINI_KEY")
    assert key_path, "GEMINI_KEY environment variable not set!"
    credentials = service_account.Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    # Refresh token
    credentials.refresh(Request())
    access_token = credentials.token

    # Call Gemini API
    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION")
    model_id = os.getenv("MODEL_ID")

    url = (
        f"https://{location}-aiplatform.googleapis.com/v1/"
        f"projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:generateContent"
    )

    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Hello Gemini test"}]}]
    }

    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.post(url, headers=headers, json=payload)

    # Assertion so pytest knows pass/fail
    assert resp.status_code == 200, f"Gemini API failed: {resp.text}"
    print(resp.json())
