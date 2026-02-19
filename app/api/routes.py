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
from app.services.llm_service import LLMService
from app.models.schemas import (
    VideoAnalysisResponse,
    AnalysisResult,
    HealthCheck,
    VideoInfo,
)
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("api_routes")

analysis_jobs = {}

video_processor = VideoProcessor(temp_dir=settings.temp_dir)
llm_service = LLMService()


@router.post("/analyze-video", response_model=VideoAnalysisResponse)
async def analyze_video(file: UploadFile = File(...)):
    try:
        logger.info(f"Received upload: {file.filename}")
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in settings.get_extensions():
            raise HTTPException(400, f"Invalid file type '{file_ext}'")
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > settings.max_file_size:
            max_mb = settings.max_file_size / 1024 / 1024
            raise HTTPException(400, f"File too large: {file_size / 1024 / 1024:.1f}MB (max {max_mb:.0f}MB)")
        job_id = str(uuid.uuid4())
        upload_path = Path(settings.upload_dir) / f"{job_id}.{file_ext}"
        upload_path.parent.mkdir(exist_ok=True)
        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Saved video: {upload_path} (job_id={job_id})")
        analysis_jobs[job_id] = AnalysisResult(job_id=job_id, status="processing", created_at=datetime.now())
        asyncio.create_task(process_video(job_id, str(upload_path)))
        logger.info(f"Started processing job: {job_id}")
        return VideoAnalysisResponse(job_id=job_id, status="processing", message="Video uploaded successfully. Processing started.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, f"Upload failed: {str(e)}")


async def process_video(job_id: str, video_path: str):
    start_time = time.time()
    try:
        logger.info(f"Processing job {job_id}")
        video_processor.validate_video(video_path)
        video_info = video_processor.get_video_info(video_path)
        analysis_jobs[job_id].video_info = VideoInfo(**video_info)
        frame_paths = video_processor.extract_frames_smart(video_path)
        analysis_jobs[job_id].num_frames_extracted = len(frame_paths)
        logger.info(f"Extracted {len(frame_paths)} frames for job {job_id}")
        
        # NEW: Analyze frames with Gemini
        description = llm_service.analyze_frames(frame_paths)
        
        processing_time = time.time() - start_time
        analysis_jobs[job_id].status = "completed"
        analysis_jobs[job_id].description = description
        analysis_jobs[job_id].processing_time = processing_time
        analysis_jobs[job_id].completed_at = datetime.now()
        logger.info(f"Job {job_id} completed in {processing_time:.2f}s")
        video_processor.cleanup_frames(frame_paths)
        Path(video_path).unlink()
    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {e}")
        analysis_jobs[job_id].status = "failed"
        analysis_jobs[job_id].error = str(e)
        analysis_jobs[job_id].completed_at = datetime.now()
        try:
            Path(video_path).unlink()
        except:
            pass


@router.get("/results/{job_id}", response_model=AnalysisResult)
async def get_results(job_id: str):
    if job_id not in analysis_jobs:
        logger.warning(f"Job not found: {job_id}")
        raise HTTPException(404, "Job not found")
    return analysis_jobs[job_id]


@router.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(status="healthy", version="1.0.0", provider=settings.llm_provider)


@router.delete("/results/{job_id}")
async def delete_result(job_id: str):
    if job_id not in analysis_jobs:
        raise HTTPException(404, "Job not found")
    del analysis_jobs[job_id]
    logger.info(f"Deleted job: {job_id}")
    return {"message": "Job deleted successfully"}