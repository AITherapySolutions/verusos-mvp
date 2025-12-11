from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import detection  # ONLY detection!

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FDA-compliant safety guardrails for therapy-adjacent companion AI applications"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ONLY detection router - nothing else
app.include_router(
    detection.router, 
    prefix=settings.API_V1_STR, 
    tags=["Detection"]
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "health": "/health",
            "detect": "/api/v1/detect",
            "docs": "/docs"
        }
    }
