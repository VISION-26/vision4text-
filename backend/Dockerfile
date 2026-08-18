FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    CUDA_VISIBLE_DEVICES=""
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 libgl1 && rm -rf /var/lib/apt/lists/*
COPY requirements-web.txt requirements-worker.txt requirements-cpu.txt requirements.txt ./
# Force CPU PyTorch first. The remaining requirements reuse these installed wheels.
RUN pip install --upgrade pip && \
    pip install -r requirements-cpu.txt && \
    pip install -r requirements.txt gunicorn
COPY . .
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/storage/uploads /app/storage/reports && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["gunicorn", "main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--workers", "1", "--bind", "0.0.0.0:8000", "--timeout", "3600"]
