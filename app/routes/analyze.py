from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(tags=["analysis"])


class AnalyzeInput(BaseModel):
    file_id: str


class AnalyzeOutput(BaseModel):
    summary: str
    pros: List[str]
    cons: List[str]
    loopholes: List[str]


# Dummy response for a known file ID
dummy_analysis = {
    "summary": "This is a summary of the document.",
    "pros": ["Pro 1", "Pro 2"],
    "cons": ["Con 1", "Con 2"],
    "loopholes": ["Loophole 1", "Loophole 2"],
}


@router.post("/analyze", response_model=AnalyzeOutput)
def analyze_document(input: AnalyzeInput):
    """
    Analyzes a previously uploaded document.

    - **file_id**: The unique identifier of the file to analyze.

    Returns a structured analysis of the document, including a summary,
    a list of pros, a list of cons, and any identified loopholes.
    """
    # For now, we'll return a dummy response if the file_id is known
    if input.file_id == "123abc":
        return dummy_analysis
    else:
        raise HTTPException(status_code=404, detail="File not found")
