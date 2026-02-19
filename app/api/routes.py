from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import uuid
from pathlib import Path
from datetime import datetime
import asyncio
import time

from app.core.config import settings
from app.services.video_processor import VideoProcessor
from app.models.schemas import (
    VideoAnalysisResponse,
    AnalysisResult,
    HealthCheck,
    VideoInfo,
)
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("api_routes")

# ──────────────────────────────────────────────────────────────
# In-memory job storage
# In production, use Redis or a database
# ──────────────────────────────────────────────────────────────
analysis_jobs = {}

# Initialize services
video_processor = VideoProcessor(temp_dir=settings.temp_dir)


# ══════════════════════════════════════════════════════════════
# ENDPOINT 1: Upload Video and Start Analysis
# ══════════════════════════════════════════════════════════════
@router.post("/analyze-video", response_model=VideoAnalysisResponse)
async def analyze_video(file: UploadFile = File(...)):
    """
    Upload a video file and start analysis.
    
    Returns immediately with a job_id.
    Use GET /results/{job_id} to check status and get results.
    """
    try:
        logger.info(f"Received upload: {file.filename}")

        # ── Validate file extension ──────────────────────────────
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.get_extensions():
            raise HTTPException(
                400,
                f"Invalid file type '{file_ext}'. "
                f"Allowed: {', '.join(settings.get_extensions())}",
            )

        # ── Check file size ───────────────────────────────────────
        file.file.seek(0, 2)  # seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # reset to start

        if file_size > settings.max_file_size:
            max_mb = settings.max_file_size / 1024 / 1024
            raise HTTPException(
                400, f"File too large: {file_size / 1024 / 1024:.1f}MB (max {max_mb:.0f}MB)"
            )

        # ── Generate job ID ───────────────────────────────────────
        job_id = str(uuid.uuid4())

        # ── Save uploaded file ────────────────────────────────────
        upload_path = Path(settings.upload_dir) / f"{job_id}.{file_ext}"
        upload_path.parent.mkdir(exist_ok=True)

        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved video: {upload_path} (job_id={job_id})")

        # ── Initialize job record ─────────────────────────────────
        analysis_jobs[job_id] = AnalysisResult(
            job_id=job_id, status="processing", created_at=datetime.now()
        )

        # ── Start background processing ───────────────────────────
        asyncio.create_task(process_video(job_id, str(upload_path)))

        logger.info(f"Started processing job: {job_id}")

        return VideoAnalysisResponse(
            job_id=job_id,
            status="processing",
            message="Video uploaded successfully. Processing started.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


# ══════════════════════════════════════════════════════════════
# BACKGROUND TASK: Process Video
# ══════════════════════════════════════════════════════════════
async def process_video(job_id: str, video_path: str):
    """
    Background task that processes the video.
    
    Steps:
    1. Validate the video
    2. Extract metadata
    3. Extract frames (smart method with scene detection)
    4. [Future: send frames to LLM for description]
    5. Store results
    6. Clean up temp files
    """
    start_time = time.time()

    try:
        logger.info(f"Processing job {job_id}")

        # ── Step 1: Validate ──────────────────────────────────────
        video_processor.validate_video(video_path)

        # ── Step 2: Get metadata ──────────────────────────────────
        video_info = video_processor.get_video_info(video_path)
        analysis_jobs[job_id].video_info = VideoInfo(**video_info)

        # ── Step 3: Extract frames (smart) ────────────────────────
        frame_paths = video_processor.extract_frames_smart(video_path)
        analysis_jobs[job_id].num_frames_extracted = len(frame_paths)

        logger.info(f"Extracted {len(frame_paths)} frames for job {job_id}")

        # ── Step 4: [LLM analysis will go here in Step 5] ─────────
        # For now, just create a placeholder description
        description = (
            f"Video analysis complete.\n"
            f"Duration: {video_info['duration']:.2f} seconds\n"
            f"Resolution: {video_info['width']}x{video_info['height']}\n"
            f"FPS: {video_info['fps']:.2f}\n"
            f"Frames extracted: {len(frame_paths)}\n"
            f"\n[AI description will be added in Step 5]"
        )

        # ── Step 5: Calculate processing time ─────────────────────
        processing_time = time.time() - start_time

        # ── Step 6: Update job with results ───────────────────────
        analysis_jobs[job_id].status = "completed"
        analysis_jobs[job_id].description = description
        analysis_jobs[job_id].processing_time = processing_time
        analysis_jobs[job_id].completed_at = datetime.now()

        logger.info(f"Job {job_id} completed in {processing_time:.2f}s")

        # ── Step 7: Cleanup ───────────────────────────────────────
        video_processor.cleanup_frames(frame_paths)
        Path(video_path).unlink()  # delete uploaded video

    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {e}")
        analysis_jobs[job_id].status = "failed"
        analysis_jobs[job_id].error = str(e)
        analysis_jobs[job_id].completed_at = datetime.now()

        # Try to cleanup
        try:
            Path(video_path).unlink()
        except:
            pass


# ══════════════════════════════════════════════════════════════
# ENDPOINT 2: Get Results
# ══════════════════════════════════════════════════════════════
@router.get("/results/{job_id}", response_model=AnalysisResult)
async def get_results(job_id: str):
    """
    Get the analysis results for a job.
    
    Status values:
    - "processing": still working on it
    - "completed": done, description is available
    - "failed": something went wrong, check error field
    """
    if job_id not in analysis_jobs:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(404, "Job not found")

    return analysis_jobs[job_id]


# ══════════════════════════════════════════════════════════════
# ENDPOINT 3: Health Check
# ══════════════════════════════════════════════════════════════
@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Check if the API is running"""
    return HealthCheck(
        status="healthy", version="1.0.0", provider=settings.llm_provider
    )


# ══════════════════════════════════════════════════════════════
# ENDPOINT 4: Delete Job Result (optional cleanup)
# ══════════════════════════════════════════════════════════════
@router.delete("/results/{job_id}")
async def delete_result(job_id: str):
    """Delete a job result from memory"""
    if job_id not in analysis_jobs:
        raise HTTPException(404, "Job not found")

    del analysis_jobs[job_id]
    logger.info(f"Deleted job: {job_id}")

    return {"message": "Job deleted successfully"}