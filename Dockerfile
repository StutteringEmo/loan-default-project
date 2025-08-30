FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY model.pkl /app/model.pkl
ENV MODEL_PATH=/app/model.pkl
EXPOSE 8080
CMD ["python","app/app.py"]

# Expose is fine; Heroku sets $PORT at runtime
EXPOSE 8080

# Use gunicorn and bind to $PORT
# (shell-form CMD so $PORT is expanded by the shell)
CMD gunicorn -w 2 -k gthread --threads 4 -b 0.0.0.0:$PORT app.app:app