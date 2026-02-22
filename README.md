# Video Analysis API

FastAPI service that analyzes videos and returns an **AI-generated description** using Google LLM model. 

---

## Features

- **Video validation** — File type, size, duration limits (via ffprobe)
- **Smart frame extraction** — Scene detection or uniform sampling
- **AI description** — Google Gemini analyzes frames and returns a summary
- **REST API** — Upload video, get job ID, poll for results

---

## Prerequisites

- **Python** 3.10+
- **FFmpeg** (includes `ffprobe`) — e.g. `brew install ffmpeg` on macOS
- **Google API key** — [Create one](https://aistudio.google.com/app/apikey) for Gemini

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/video_analysis_project.git
cd video-analysis-api
```

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with at least:

```env
GOOGLE_API_KEY=your_key_here
LLM_PROVIDER=google
```

You can also set `UPLOAD_DIR`, `MAX_VIDEO_DURATION`, `ALLOWED_EXTENSIONS`, `FFPROBE_PATH`, etc. See Configuration below.

---

## How to use this software

You run the API server, then use **`run_video_analysis.py`** to upload a video and print the AI description in the terminal.

### 1. Start the API server

In a terminal:

```bash
cd video-analysis-api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Leave this running. You should see something like: `Uvicorn running on http://127.0.0.1:8000`.

### 2. Run the client with a video file

In **another** terminal:

```bash
cd video-analysis-api
source .venv/bin/activate
python run_video_analysis.py <path/to/your/video.mp4>
```

**Example:**

```bash
python run_video_analysis.py uploads/test_video.mp4
```

### 3. What you see

- Health check (API and provider)
- Upload confirmation and job ID
- Wait for processing (about 10–30 seconds for Gemini)
- **Results:** video info (duration, resolution, FPS), processing stats, and the **AI description** of the video printed in the terminal

The script talks to `http://localhost:8000`. If the server is not running, you’ll get a connection error and a reminder to start it.

---

## API docs (optional)

With the server running, open in a browser:

- **Swagger UI:** http://localhost:8000/docs  
- **ReDoc:** http://localhost:8000/redoc  

You can upload a video and check results via the web UI.

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
│   │   └── llm_service.py     # Gemini integration
│   └── utils/logger.py
├── run_video_analysis.py     # Run script – upload video and print AI description
├── requirements.txt
├── .env                      # Not committed; add GOOGLE_API_KEY
└── README.md
```

---

## Configuration

| Variable              | Default   | Description                    |
|-----------------------|-----------|--------------------------------|
| `GOOGLE_API_KEY`      | —         | **Required** for AI description |
| `LLM_PROVIDER`        | google    | Must be `google` for Gemini     |
| `MAX_VIDEO_DURATION`  | 300       | Max video length (seconds)     |
| `ALLOWED_EXTENSIONS`  | mp4,...   | Allowed video extensions        |
| `FFPROBE_PATH`        | ffprobe   | Path to ffprobe binary          |

---

## License

Education usage is permitted.
