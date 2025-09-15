from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.process_document import router as process_document_router
from app.routes.documents import router as documents_router

app = FastAPI(
    title="Legal Document Analyzer API",
    version="1.0.0",
    description="An API to upload, analyze, and manage legal documents."
)

# Include all the routers
app.include_router(health_router)
app.include_router(process_document_router)
app.include_router(documents_router)

@app.get("/", tags=["root"])
def read_root():
    return {"message": "Welcome to the Legal Document Analyzer API"}
