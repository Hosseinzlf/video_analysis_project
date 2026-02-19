from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


class Settings(BaseSettings):
    # API Keys
    google_api_key: str = ""

    # Provider
    llm_provider: str = "google"

    # Directories
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    temp_dir: str = "temp"
    log_dir: str = "logs"

    # File settings
    max_file_size: int = 100000000
    allowed_extensions: str = "mp4,avi,mov,mkv,webm"

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

    # Optional: path to ffprobe binary (if not on PATH)
    ffprobe_path: str = "ffprobe"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def get_extensions(self) -> List[str]:
        """Parse comma-separated extensions into a list.
        Handles both plain (mp4,avi,...) and JSON-style (["mp4","avi",...]) env values.
        """
        raw = [e.strip() for e in self.allowed_extensions.split(",")]
        return [e.strip('[]"\'') for e in raw if e.strip('[]"\'')]


settings = Settings()

# Auto-create directories
for directory in [
    settings.upload_dir,
    settings.output_dir,
    settings.temp_dir,
    settings.log_dir,
]:
    Path(directory).mkdir(exist_ok=True)