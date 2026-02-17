from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    # Provider
    llm_provider: str = "local"

    # Directories
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    temp_dir: str = "temp"
    log_dir: str = "logs"

    # File settings
    max_file_size: int = 100000000
    allowed_extensions: List[str] = ["mp4", "avi", "mov", "mkv", "webm"]

    # Processing settings
    max_video_duration: int = 300
    min_frames: int = 5
    max_frames: int = 15
    default_frames: int = 10

    # Scene detection
    scene_threshold: float = 27.0
    min_scene_length: int = 15

    # Frame quality
    frame_quality: int = 85
    max_frame_dimension: int = 1920

    # FFmpeg/ffprobe (optional: set FFPROBE_PATH if not on PATH, e.g. /opt/homebrew/bin/ffprobe)
    ffprobe_path: str = "ffprobe"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Auto-create directories
for directory in [
    settings.upload_dir,
    settings.output_dir,
    settings.temp_dir,
    settings.log_dir,
]:
    Path(directory).mkdir(exist_ok=True)