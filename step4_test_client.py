"""
STEP 4 TEST CLIENT
Location: video-analysis-api/step4_test_client.py

This script tests the running API server by uploading a video.

BEFORE running this:
    1. Start the server in another terminal:
       uvicorn app.main:app --reload --port 8000
    
    2. Then run this script:
       python step4_test_client.py uploads/test_video.mp4

Usage:
    python step4_test_client.py path/to/video.mp4
"""

import sys
import time
import requests
from pathlib import Path

PASS = "✅"
FAIL = "❌"

# ══════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════
API_URL = "http://localhost:8000"

# ══════════════════════════════════════════════════════════════
# Get video path from command line
# ══════════════════════════════════════════════════════════════
if len(sys.argv) < 2:
    print(f"\n{FAIL} Please provide a video file:")
    print("  python step4_test_client.py uploads/test_video.mp4\n")
    sys.exit(1)

video_path = Path(sys.argv[1])

if not video_path.exists():
    print(f"\n{FAIL} Video file not found: {video_path}\n")
    sys.exit(1)

print("\n" + "=" * 55)
print("  STEP 4 API TEST: Testing Live Server")
print("=" * 55)
print(f"\n  API URL    : {API_URL}")
print(f"  Video file : {video_path}")
print()

# ══════════════════════════════════════════════════════════════
# Test 1: Health Check
# ══════════════════════════════════════════════════════════════
print("[1] Testing health check endpoint...")

try:
    response = requests.get(f"{API_URL}/api/v1/health", timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print(f"  {PASS} Health check passed")
        print(f"       Status  : {data['status']}")
        print(f"       Version : {data['version']}")
        print(f"       Provider: {data['provider']}")
    else:
        print(f"  {FAIL} Health check failed: {response.status_code}")
        sys.exit(1)

except requests.exceptions.ConnectionError:
    print(f"  {FAIL} Cannot connect to API server!")
    print(f"\n  Please start the server first:")
    print(f"    uvicorn app.main:app --reload --port 8000\n")
    sys.exit(1)
except Exception as e:
    print(f"  {FAIL} Health check error: {e}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# Test 2: Upload Video
# ══════════════════════════════════════════════════════════════
print("\n[2] Uploading video...")

try:
    with open(video_path, "rb") as f:
        files = {"file": (video_path.name, f, "video/mp4")}
        response = requests.post(
            f"{API_URL}/api/v1/analyze-video", files=files, timeout=30
        )

    if response.status_code == 200:
        data = response.json()
        job_id = data["job_id"]
        print(f"  {PASS} Video uploaded successfully")
        print(f"       Job ID  : {job_id}")
        print(f"       Status  : {data['status']}")
        print(f"       Message : {data['message']}")
    else:
        print(f"  {FAIL} Upload failed: {response.status_code}")
        print(f"       {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"  {FAIL} Upload error: {e}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# Test 3: Poll for Results
# ══════════════════════════════════════════════════════════════
print("\n[3] Waiting for processing to complete...")

max_wait = 30  # seconds
poll_interval = 2  # seconds
elapsed = 0

while elapsed < max_wait:
    time.sleep(poll_interval)
    elapsed += poll_interval

    try:
        response = requests.get(
            f"{API_URL}/api/v1/results/{job_id}", timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            status = data["status"]

            if status == "completed":
                print(f"  {PASS} Processing completed!")
                print(f"\n  Results:")
                print(f"       Job ID     : {data['job_id']}")
                print(f"       Status     : {data['status']}")
                
                if data.get("video_info"):
                    info = data["video_info"]
                    print(f"       Duration   : {info['duration']:.2f}s")
                    print(f"       Resolution : {info['width']}x{info['height']}")
                    print(f"       FPS        : {info['fps']:.2f}")
                
                print(f"       Frames     : {data.get('num_frames_extracted', 'N/A')}")
                print(f"       Proc. time : {data.get('processing_time', 0):.2f}s")
                
                if data.get("description"):
                    desc = data["description"]
                    print(f"\n  Description:")
                    for line in desc.split("\n"):
                        print(f"       {line}")
                    print(f"\n  [Full description text]:")
                    print(desc)
                
                break

            elif status == "failed":
                print(f"  {FAIL} Processing failed!")
                print(f"       Error: {data.get('error', 'Unknown error')}")
                sys.exit(1)

            else:  # still processing
                print(f"       Status: {status} (waiting {elapsed}s...)")

        else:
            print(f"  {FAIL} Failed to get results: {response.status_code}")
            sys.exit(1)

    except Exception as e:
        print(f"  {FAIL} Error checking results: {e}")
        sys.exit(1)

else:
    print(f"  {FAIL} Timeout after {max_wait}s")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
# Success!
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 55)
print(f"  {PASS} All API tests passed!")
print(f"\n  Your API is working correctly.")
print(f"  Next: Add LLM integration in Step 5")
print("=" * 55 + "\n")