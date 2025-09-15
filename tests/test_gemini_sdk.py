import os
import pytest
import vertexai
from vertexai.preview.generative_models import GenerativeModel

@pytest.mark.skipif(os.getenv("GEMINI_KEY") is None, reason="GEMINI_KEY not set")
def test_gemini_sdk():
    # Set credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GEMINI_KEY")

    # Init SDK
    vertexai.init(project=os.getenv("PROJECT_ID"), location=os.getenv("LOCATION"))

    # Load model
    model = GenerativeModel("gemini-2.5-pro")

    # Generate test content
    resp = model.generate_content("Hello Gemini test!")

    # Assert we got some text back
    text = resp.text if hasattr(resp, "text") else str(resp)
    assert text, "Gemini SDK returned empty response"
