from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.process_document import router as process_document_router
from app.routes.documents import router as documents_router
from app.routes.analyze import router as analyze_router

app = FastAPI(title="Legal Document Analyzer API", version="0.1.0")

# Include route files
app.include_router(health_router)
app.include_router(process_document_router)
app.include_router(documents_router)
app.include_router(analyze_router)
