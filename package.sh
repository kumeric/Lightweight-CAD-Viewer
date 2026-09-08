#!/usr/bin/env bash
# Saves the built cadviewer image as a tar file.
# You can move this file to other WSL2/Linux/Docker Desktop environments 
# and use it immediately with `docker load -i cadviewer.tar`.
set -euo pipefail

cd "$(dirname "$0")"

IMAGE_NAME="cadviewer:latest"
OUT_FILE="cadviewer.tar"

echo "[1/2] Building image..."
docker compose build

echo "[2/2] Saving image to ${OUT_FILE}..."
docker save "${IMAGE_NAME}" -o "${OUT_FILE}"

echo "Done: ${OUT_FILE}"
echo "How to use on other systems: Run 'docker load -i ${OUT_FILE}', then use run.sh or docker compose"