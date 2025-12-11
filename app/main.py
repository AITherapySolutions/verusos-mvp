from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import detection, company, dashboard, protocol, review, export

Base.metadata.create_all(bind=engine)

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

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(
    detection.router, 
    prefix=settings.API_V1_STR, 
    tags=["Detection"]
)
app.include_router(
    company.router, 
    prefix=settings.API_V1_STR, 
    tags=["Company"]
)
app.include_router(
    dashboard.router, 
    tags=["Dashboard"]
)
app.include_router(
    protocol.router,
    prefix="/api/v1/protocol",
    tags=["Protocol"]
)
app.include_router(
    review.router,
    prefix="/api/v1/review",
    tags=["Compliance Review"]
)
app.include_router(
    export.router,
    prefix="/api/v1/export",
    tags=["Export"]
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@app.get("/api/v1")
async def api_info():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "detect": "/api/v1/detect",
            "report_response": "/api/v1/report-response",
            "companies": "/api/v1/companies",
            "dashboard_stats": "/dashboard/stats",
            "dashboard_alerts": "/dashboard/alerts",
            "dashboard": "/"
        }
    }
