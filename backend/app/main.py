"""
FastAPI Main Application
Document Processing API with AG-UI Protocol
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import auth, documents
import os

# Phoenix Tracing Setup
if not os.environ.get("PHOENIX_TRACER_REGISTERED"):
    from phoenix.otel import register
    
    if settings.PHOENIX_API_KEY and settings.PHOENIX_COLLECTOR_ENDPOINT:
        tracer_provider = register(
            project_name="document-processing-api",
            endpoint=settings.PHOENIX_COLLECTOR_ENDPOINT,
            auto_instrument=True
        )
        os.environ["PHOENIX_TRACER_REGISTERED"] = "1"
        print("[*] Phoenix tracing enabled for API")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered document processing API with AG-UI Protocol for agent-user interactions"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(documents.router)

@app.get("/")
async def root():
    """API Root - Health check"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "features": [
            "User Authentication (Supabase)",
            "Document Upload & Storage",
            "AI Document Classification",
            "Invoice/Receipt/PO Extraction",
            "AG-UI Protocol for Agent Interactions",
            "Phoenix Tracing & Monitoring"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "phoenix_tracing": os.environ.get("PHOENIX_TRACER_REGISTERED") == "1"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
