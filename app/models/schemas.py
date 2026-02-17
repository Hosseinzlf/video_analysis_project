from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoAnalysisResponse(BaseModel):
    job_id: str
    status: str
    message: str


class VideoInfo(BaseModel):
    duration: float
    width: int
    height: int
    fps: float
    total_frames: int
    format: str


class AnalysisResult(BaseModel):
    job_id: str
    status: str                            # processing | completed | failed
    description: Optional[str] = None
    video_info: Optional[VideoInfo] = None
    num_frames_extracted: Optional[int] = None
    num_scenes_detected: Optional[int] = None
    processing_time: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class HealthCheck(BaseModel):
    status: str
    version: str
    provider: str




## Final Structure After Step 1
"""
video-analysis-api/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           ← File 3
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          ← File 5
│   ├── services/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py           ← File 4
├── uploads/
├── outputs/
├── temp/
├── logs/
├── .env                        ← File 2
└── requirements.txt            ← File 1
"""