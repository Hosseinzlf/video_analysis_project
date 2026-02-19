"""
Video Analysis API – Run client

Upload a video to the API and print the AI-generated description.

Prerequisites:
  1. Set GOOGLE_API_KEY in .env (get key from https://aistudio.google.com/app/apikey)
  2. Start the server in another terminal: uvicorn app.main:app --reload --port 8000

Usage:
  python run_video_analysis.py <path/to/video.mp4>

Example:
  python run_video_analysis.py uploads/test_video.mp4
"""

import sys
import time
import requests
from pathlib import Path

PASS = "✅"
FAIL = "❌"

API_URL = "http://localhost:8000"

if len(sys.argv) < 2:
    print(f"\n{FAIL} Please provide a video file:")
    print("  python run_video_analysis.py uploads/test_video.mp4\n")
    sys.exit(1)

video_path = Path(sys.argv[1])

if not video_path.exists():
    print(f"\n{FAIL} Video file not found: {video_path}\n")
    sys.exit(1)

print("\n" + "=" * 60)
print("  Video Analysis API – AI description")
print("=" * 60)
print(f"\n  API URL    : {API_URL}")
print(f"  Video file : {video_path}")
print()

# Health check
print("[1] Testing health check...")

try:
    response = requests.get(f"{API_URL}/api/v1/health", timeout=5)

    if response.status_code == 200:
        data = response.json()
        print(f"  {PASS} Health check passed")
        print(f"       Status  : {data['status']}")
        print(f"       Version : {data['version']}")
        print(f"       Provider: {data['provider']}")

        if data['provider'] != 'google':
            print(f"\n  ⚠️  Warning: Provider is '{data['provider']}', expected 'google'")
            print(f"       Set LLM_PROVIDER=google and GOOGLE_API_KEY in .env")
    else:
        print(f"  {FAIL} Health check failed: {response.status_code}")
        sys.exit(1)

except requests.exceptions.ConnectionError:
    print(f"  {FAIL} Cannot connect to API server!")
    print(f"\n  Start the server first in another terminal:")
    print(f"    uvicorn app.main:app --reload --port 8000\n")
    sys.exit(1)
except Exception as e:
    print(f"  {FAIL} Health check error: {e}")
    sys.exit(1)

# Upload video
print("\n[2] Uploading video...")

try:
    with open(video_path, "rb") as f:
        files = {"file": (video_path.name, f, "video/mp4")}
        response = requests.post(
            f"{API_URL}/api/v1/analyze-video",
            files=files,
            timeout=30
        )

    if response.status_code == 200:
        data = response.json()
        job_id = data["job_id"]
        print(f"  {PASS} Video uploaded successfully")
        print(f"       Job ID : {job_id}")
        print(f"       Status : {data['status']}")
    else:
        print(f"  {FAIL} Upload failed: {response.status_code}")
        print(f"       {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"  {FAIL} Upload error: {e}")
    sys.exit(1)

# Wait for AI analysis
print("\n[3] Waiting for AI analysis to complete...")
print("    (This may take 10-30 seconds for Gemini API)")

max_wait = 90
poll_interval = 3
results_timeout = 45
elapsed = 0

while elapsed < max_wait:
    time.sleep(poll_interval)
    elapsed += poll_interval

    try:
        response = requests.get(
            f"{API_URL}/api/v1/results/{job_id}",
            timeout=results_timeout
        )

        if response.status_code == 200:
            data = response.json()
            status = data["status"]

            if status == "completed":
                print(f"\n  {PASS} AI analysis completed!\n")
                print("=" * 60)
                print("  RESULTS")
                print("=" * 60)

                print(f"\n  Job ID      : {data['job_id']}")
                print(f"  Status      : {data['status']}")

                if data.get("video_info"):
                    info = data["video_info"]
                    print(f"\n  Video Info:")
                    print(f"    Duration   : {info['duration']:.2f}s")
                    print(f"    Resolution : {info['width']}x{info['height']}")
                    print(f"    FPS        : {info['fps']:.2f}")
                    print(f"    Format     : {info['format']}")

                print(f"\n  Processing:")
                print(f"    Frames     : {data.get('num_frames_extracted', 'N/A')}")
                print(f"    Time       : {data.get('processing_time', 0):.2f}s")

                if data.get("description"):
                    print(f"\n  AI Description:")
                    print("  " + "─" * 58)
                    desc_lines = data["description"].split("\n")
                    for line in desc_lines:
                        if line.strip():
                            if len(line) > 56:
                                words = line.split()
                                current_line = "  "
                                for word in words:
                                    if len(current_line) + len(word) + 1 <= 58:
                                        current_line += word + " "
                                    else:
                                        print(current_line)
                                        current_line = "  " + word + " "
                                if current_line.strip():
                                    print(current_line)
                            else:
                                print(f"  {line}")
                        else:
                            print()
                    print("  " + "─" * 58)
                else:
                    print(f"\n  {FAIL} No description generated!")

                break

            elif status == "failed":
                print(f"\n  {FAIL} Processing failed!")
                print(f"       Error: {data.get('error', 'Unknown error')}")
                sys.exit(1)

            else:
                print(f"       {status}... ({elapsed}s elapsed)")

        else:
            print(f"  {FAIL} Failed to get results: {response.status_code}")
            sys.exit(1)

    except Exception as e:
        print(f"  {FAIL} Error checking results: {e}")
        sys.exit(1)

else:
    print(f"\n  {FAIL} Timeout after {max_wait}s")
    print(f"       The job may still be processing.")
    print(f"       Check: GET {API_URL}/api/v1/results/{job_id}")
    sys.exit(1)

print("\n" + "=" * 60)
print(f"  {PASS} Done!")
print("=" * 60 + "\n")
