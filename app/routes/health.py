from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Returns a simple health check response to confirm the API is running."""
    return HealthResponse(status="ok")
