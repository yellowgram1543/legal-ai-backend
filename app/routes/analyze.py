from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["analysis"])


# Input model
class AnalyzeInput(BaseModel):
    file_id: str


# Output model
class AnalyzeOutput(BaseModel):
    summary: str
    pros: list
    cons: list
    loopholes: list


# Dummy in-memory "file database"
file_data = {
    "file123": {
        "summary": "This is a summary of the document.",
        "pros": ["Clear terms and conditions", "Well-defined responsibilities"],
        "cons": ["Complex language", "Ambiguous timelines"],
        "loopholes": ["No penalty for non-compliance"],
    }
}


@router.post("/analyze", response_model=AnalyzeOutput)
def analyze_document(input: AnalyzeInput):
    """
    Analyze a document based on a given file ID.
    Returns a summary, pros, cons, and loopholes in the document.
    """
    # Lookup the file in the dummy database
    analysis = file_data.get(input.file_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="File not found")

    return analysis
