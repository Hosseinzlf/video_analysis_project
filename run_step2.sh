#!/usr/bin/env bash
# Run step2 validation with the video-analysis-api conda env Python (no need to activate env)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-/opt/anaconda3/envs/video-analysis-api/bin/python}"
exec "$PYTHON" "$SCRIPT_DIR/step2_validation.py" "$@"
