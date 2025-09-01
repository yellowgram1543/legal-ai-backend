from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health():
    """
    Endpoint to verify service status.
    Returns a 'healthy' status message if the service is running.
    """
    return {"status": "healthy"}
