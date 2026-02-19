from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("main")

# ══════════════════════════════════════════════════════════════
# Create FastAPI app
# ══════════════════════════════════════════════════════════════
app = FastAPI(
    title="Video Analysis API",
    description="AI-powered video analysis using scene detection",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI at /docs
    redoc_url="/redoc",    # ReDoc at /redoc
)

# ══════════════════════════════════════════════════════════════
# CORS middleware - allows requests from any origin
# In production, restrict this to specific domains
# ══════════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════
# Include API routes with /api/v1 prefix
# ══════════════════════════════════════════════════════════════
app.include_router(router, prefix="/api/v1", tags=["video-analysis"])


# ══════════════════════════════════════════════════════════════
# Startup event
# ══════════════════════════════════════════════════════════════
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 55)
    logger.info("Video Analysis API Starting")
    logger.info(f"Provider       : {settings.llm_provider}")
    logger.info(f"Max frames     : {settings.max_frames}")
    logger.info(f"Scene threshold: {settings.scene_threshold}")
    logger.info(f"Upload dir     : {settings.upload_dir}")
    logger.info(f"Temp dir       : {settings.temp_dir}")
    logger.info("=" * 55)


# ══════════════════════════════════════════════════════════════
# Shutdown event
# ══════════════════════════════════════════════════════════════
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Video Analysis API Shutting Down")


# ══════════════════════════════════════════════════════════════
# Root endpoint
# ══════════════════════════════════════════════════════════════
@app.get("/")
async def root():
    """
    Root endpoint - shows basic info and links
    """
    return {
        "message": "Video Analysis API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/health",
            "upload": "POST /api/v1/analyze-video",
            "results": "GET /api/v1/results/{job_id}",
        },
    }