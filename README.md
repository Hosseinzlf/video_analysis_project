# Video Analysis API

A FastAPI-based service for video analysis: validation, metadata extraction, scene detection, and smart frame extraction. Designed to support AI-powered video understanding (e.g., summaries, captions) via extracted keyframes.

---

## Features

- **Video validation** — Check file existence, duration limits, and readability
- **Metadata extraction** — Duration, resolution, FPS, total frames, format (via ffprobe)
- **Frame extraction** — Uniform sampling or scene-based keyframes
- **Scene detection** — Detect scene changes using histogram comparison (HSV)
- **Smart extraction** — Combines scene detection with configurable min/max frame counts
- **Configurable** — Limits, paths, and thresholds via `.env`

---

## Tech Stack

| Category        | Stack                    |
|----------------|--------------------------|
| API            | FastAPI, Uvicorn         |
| Video          | OpenCV, ffmpeg-python    |
| Scene detection| scenedetect, OpenCV      |
| AI/ML (planned)| OpenAI, Google GenAI      |
| Config         | Pydantic Settings, dotenv |

---

## Prerequisites

- **Python** 3.10+
- **FFmpeg** (includes `ffprobe`) — [Install](https://ffmpeg.org/download.html) (e.g. `brew install ffmpeg` on macOS)
- **Conda** (recommended) or venv for isolation

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd video-analysis-api
```

### 2. Create and activate environment

**Conda:**

```bash
conda create -n video-analysis-api python=3.11
conda activate video-analysis-api
```

**venv:**

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment configuration

Copy the example env (if present) or create `.env` in the project root:

```env
# Directories
UPLOAD_DIR=uploads
OUTPUT_DIR=outputs
TEMP_DIR=temp
LOG_DIR=logs

# Video limits
MAX_VIDEO_DURATION=300
MAX_FILE_SIZE=100000000
ALLOWED_EXTENSIONS=["mp4","avi","mov","mkv","webm"]

# Frames
MIN_FRAMES=5
MAX_FRAMES=15
DEFAULT_FRAMES=10
FRAME_QUALITY=85
MAX_FRAME_DIMENSION=1920

# Scene detection
SCENE_THRESHOLD=27.0
MIN_SCENE_LENGTH=15

# Optional: if ffprobe is not on PATH (e.g. macOS after brew install ffmpeg)
# FFPROBE_PATH=/opt/homebrew/bin/ffprobe
```

---

## Project Structure

```
video-analysis-api/
├── app/
│   ├── core/
│   │   └── config.py          # Settings and env loading
│   ├── models/
│   │   └── schemas.py          # Pydantic models for API
│   ├── services/
│   │   ├── video_processor.py  # Validation, metadata, frame extraction
│   │   └── scene_detector.py   # Scene detection and keyframes
│   └── utils/
│       └── logger.py           # Logging setup
├── uploads/                    # Video upload directory
├── outputs/                    # Analysis outputs
├── temp/                       # Temporary frame extraction
├── logs/                       # Application logs
├── .env                        # Local config (not committed)
├── requirements.txt
└── README.md
```

---

## Usage

### Running the API (when implemented)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Using the services in code

```python
from app.services.video_processor import VideoProcessor
from app.services.scene_detector import SceneDetector

# Validate and get metadata
processor = VideoProcessor()
processor.validate_video("uploads/my_video.mp4")
info = processor.get_video_info("uploads/my_video.mp4")

# Scene-based frame extraction
frames = processor.extract_frames_smart("uploads/my_video.mp4")
# ... use frames for AI analysis ...
processor.cleanup_frames(frames)
```

---

## Configuration Reference

| Variable              | Default   | Description                    |
|-----------------------|-----------|--------------------------------|
| `MAX_VIDEO_DURATION`  | 300       | Max video length (seconds)     |
| `MIN_FRAMES` / `MAX_FRAMES` | 5 / 15 | Frame count bounds for smart extraction |
| `SCENE_THRESHOLD`     | 27.0      | Scene change sensitivity      |
| `FRAME_QUALITY`       | 85        | JPEG quality for extracted frames |
| `FFPROBE_PATH`        | ffprobe   | Path to ffprobe binary         |

---

## License

MIT (or your chosen license.)
