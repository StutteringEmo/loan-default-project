FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Minimal packages for building wheels, then clean up apt cache
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Make sure pip/setuptools are current before installing pinned reqs
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY model.pkl /app/model.pkl
ENV MODEL_PATH=/app/model.pkl

EXPOSE 8080

# Gunicorn behind Heroku/Docker
CMD gunicorn -w 2 -k gthread --threads 4 -b 0.0.0.0:$PORT app.app:app
