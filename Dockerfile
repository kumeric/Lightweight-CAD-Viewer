# syntax=docker/dockerfile:1
FROM python:3.11-slim

# ---------------------------------------------------------------------------
# System libraries required to display the GUI (Qt/VTK) via X11
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libglu1-mesa \
    libegl1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxrender1 \
    libxi6 \
    libsm6 \
    libice6 \
    libdbus-1-3 \
    libfontconfig1 \
    libnss3 \
    fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py /app/app.py

# Shared directory for opening files inside the container (mounted as a volume in docker-compose)
RUN mkdir -p /data
WORKDIR /data

ENV QT_X11_NO_MITSHM=1

# WSLg supports hardware acceleration (GPU) by default. 
# In case of compatibility issues, you can force software rendering using `docker run -e LIBGL_ALWAYS_SOFTWARE=1 ...`

ENTRYPOINT ["python", "/app/app.py"]