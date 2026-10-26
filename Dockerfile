# syntax=docker/dockerfile:1
# YOLO Vision Lab — image GPU (NVIDIA). Les wheels PyTorch cu128 embarquent CUDA/cuDNN :
# seul le pilote NVIDIA de l'hôte est nécessaire (+ NVIDIA Container Toolkit sous Linux).
# Build CPU uniquement : docker build --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cpu .
FROM python:3.14-slim-bookworm

ARG TORCH_INDEX=https://download.pytorch.org/whl/cu128

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VIEW=web \
    MODELS_DIR=/app/models \
    OUTPUT_DIR=/app/output \
    YOLO_CONFIG_DIR=/app/models/.ultralytics

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install torch torchvision --index-url ${TORCH_INDEX}
COPY requirements.txt requirements-football.txt ./
RUN pip install -r requirements.txt -r requirements-football.txt \
    && pip install --force-reinstall --no-deps opencv-python-headless

COPY vision_lab ./vision_lab
COPY projets ./projets
COPY zones ./zones

EXPOSE 8080 8000
ENTRYPOINT ["python", "-m", "vision_lab"]
CMD ["distance_vitesse"]
