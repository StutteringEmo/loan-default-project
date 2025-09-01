# -------- Base image --------
FROM python:3.11-slim

# Avoid prompts at install time
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (build-essential only if needed; remove if wheels are enough)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# -------- Workdir --------
WORKDIR /app

# -------- Python deps (cached layer) --------
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# -------- Project files --------
# Copy everything needed for the API to run
COPY app/ /app/app/
COPY model.pkl /app/model.pkl
COPY schema.json /app/schema.json
COPY sample_request.json /app/sample_request.json

# ------- Runtime env --------
ENV MODEL_PATH=/app/model.pkl

# Heroku sets $PORT dynamically; fall back to 8080 for local testing
CMD ["gunicorn", "app.app:app", "--bind", "0.0.0.0:${PORT:-8080}", "--workers=2", "--threads=4", "--timeout=60"]
