#!/usr/bin/env bash
# Builds (only if missing) and runs the CAD Viewer Docker container in a WSL2 + WSLg environment.
set -euo pipefail

cd "$(dirname "$0")"

mkdir -p examples

# Adjust default WSLg environment variables (usually set automatically in WSL2)
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/mnt/wslg/runtime-dir}"

IMAGE_NAME="cadviewer:latest"

# 1. Check if the Docker image already exists. If not, build it.
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "[1/2] Image not found. Building image (first-time execution may take several minutes)..."
    docker compose build
else
    echo "[1/2] Image already exists. Skipping build step."
fi

# 2. Run the CAD Viewer
echo "[2/2] Running CAD Viewer..."
if [ "${1:-}" != "" ]; then
    # Example: ./run.sh examples/part.step -> Opens inside the container as /data/part.step
    FILE_ARG="/data/$(basename "$1")"
    cp -f "$1" "./examples/$(basename "$1")" 2>/dev/null || true
    docker compose run --rm cadviewer "$FILE_ARG"
else
    docker compose run --rm cadviewer
fi