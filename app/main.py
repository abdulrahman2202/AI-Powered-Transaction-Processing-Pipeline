# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import router as api_router
from core.logging import setup_logging
from core.config import settings

# Setup system logging
setup_logging()

app = FastAPI(
    title="AI-Powered Transaction Processing Pipeline",
    description="Asynchronous financial transaction data cleaning, anomaly detection, and Gemini-powered categorization API.",
    version="1.0.0"
)

# Enable CORS for convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include jobs router
app.include_router(api_router)

@app.get("/", tags=["General"])
def root():
    """Welcome and health check endpoint."""
    return {
        "status": "healthy",
        "message": "AI-Powered Transaction Processing Pipeline API is running.",
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs"
    }
