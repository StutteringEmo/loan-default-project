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

# -------- Runtime env --------
# The Flask app expects MODEL_PATH env; we point it at /app/model.pkl
ENV MODEL_PATH=/app/model.pkl \
    PORT=8080

EXPOSE 8080

# -------- Entrypoint (gunicorn, production grade) --------
# If your Flask app instance is named `app` inside app/app.py, the WSGI target is app.app:app
CMD ["gunicorn", "app.app:app", "--bind", "0.0.0.0:8080", "--workers=2", "--threads=4", "--timeout=60"]
