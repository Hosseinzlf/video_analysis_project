# Video Analysis API

FastAPI service that analyzes videos and returns an **AI-generated description** using Google LLM model. 


---

## Features

- **Video validation** — File type, size, duration limits (via ffprobe)
- **Smart frame extraction** — Scene detection 
- **AI description** — Google Gemini analyzes frames and returns a summary


---

## Prerequisites

- **Python 3.10+** — check with `python3 --version`
- **FFmpeg** (includes `ffprobe`):
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **Google Gemini API key** — get one free at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## Installation

```bash
git clone https://github.com/Hosseinzlf/video_analysis_project.git
cd video_analysis_project/video-analysis-api
```

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file by copying the provided example:

```bash
cp .env.example .env
```

Then open `.env` and set your API key:

```env
GOOGLE_API_KEY=your_key_here
LLM_PROVIDER=google
```

All other values in `.env.example` have sensible defaults and can be left as-is.

---

## How to use this software

You run the API server, then use **`run_video_analysis.py`** to upload a video and print the AI description in the terminal.

### 1. Start the API server

In a terminal:

```bash
source .venv/bin/activate      # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Leave this running. You should see: `Uvicorn running on http://127.0.0.1:8000`.

### 2. Run the client with a video file

In a **second terminal**, point the script at any video file you have:

```bash
source .venv/bin/activate      # Windows: .venv\Scripts\activate
python run_video_analysis.py /path/to/any/video.mp4
```

Supported formats: `mp4`, `avi`, `mov`, `mkv`, `webm` — max 100 MB, max 5 minutes.

### 3. What you will see in the terminal

- Health check confirming the API and Gemini are reachable
- Upload confirmation and job ID
- Progress polling (processing takes ~10–30 seconds)
- **Final result:** video info (duration, resolution, FPS) + the **AI-generated description**

> If the server is not running you will get a connection error — make sure Step 1 is running first.

---

## API docs (optional)

With the server running, open in a browser:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You can upload a video and check results directly from the browser UI.

---

## Project structure

```
video-analysis-api/
├── app/
│   ├── api/routes.py         # Endpoints: upload, results, health
│   ├── core/config.py        # Settings from .env
│   ├── models/schemas.py     # Pydantic models
│   ├── services/
│   │   ├── video_processor.py
│   │   ├── scene_detector.py
│   │   └── llm_service.py    # Gemini integration
│   └── utils/logger.py
├── run_video_analysis.py     # CLI client — upload video and print AI description
├── requirements.txt
├── .env.example              # Copy to .env and fill in your API key
└── README.md
```

---

## Configuration

| Variable             | Default     | Description                         |
|----------------------|-------------|-------------------------------------|
| `GOOGLE_API_KEY`     | —           | **Required.** Your Gemini API key   |
| `LLM_PROVIDER`       | google      | Must be `google`                    |
| `MAX_VIDEO_DURATION` | 300         | Max video length in seconds         |
| `ALLOWED_EXTENSIONS` | mp4,...     | Comma-separated allowed formats     |
| `MAX_FILE_SIZE`      | 100000000   | Max upload size in bytes (100 MB)   |
| `FFPROBE_PATH`       | ffprobe     | Full path to ffprobe if not on PATH |

---

## License

Education usage is permitted.
