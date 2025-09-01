# Loan Default Prediction with SageMaker  

[![CI](https://github.com/stutteringemo/loan-default-project/actions/workflows/ci.yml/badge.svg)](https://github.com/stutteringemo/loan-default-project/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)


This project demonstrates an end-to-end **machine learning pipeline** for predicting loan defaults.  
The workflow covers everything from **local training → container packaging → SageMaker deployment → Kubernetes scaling**.  

---

## Project Overview  
- **Goal:** Predict whether a loan applicant is likely to default.  
- **Dataset:** Public loan dataset with features like credit lines, loan amount, interest rate, employment type, etc.  
- **ML Algorithm:** Scikit-learn pipeline with Logistic Regression.  
- **Deployment:**  
  1. Local training and packaging (`model.pkl`, `inference.py`, `requirements.txt`)  
  2. Containerized deployment (Flask/Gunicorn)  
  3. CI/CD with Heroku for testing  
  4. AWS SageMaker real-time endpoint  
  5. Kubernetes manifests for scalable hosting  

---

## Repository Structure  

- **app/** → Flask app for local testing  
- **notebooks/** → Jupyter notebooks for EDA, training, and evaluation  
- **sm_model/** → SageMaker model folder  
  - `model.pkl` → Trained model file  
  - **code/** → Code dependencies for SageMaker  
    - `inference.py` → Inference script for model serving  
    - `requirements.txt` → Dependencies for SageMaker container  
- **Dockerfile** → Container image definition for deployment  
- **requirements.txt** → Project-level dependencies for local dev  
- **model.tar.gz** → Packaged model archive for SageMaker  
- **schema.json** → Defines input schema for requests  
- **sample_request.json** → Example request payload  

---

## Deployment Options  

### 1) Flask (Local)

**Files you need**
- `app/app.py`
- `app/templates/index.html`
- `app/static/css/style.css`
- `requirements.txt`
- `model.pkl`  ← at repo root (or set `MODEL_PATH` if elsewhere)
- `schema.json` and `sample_request.json`  ← at repo root

**Steps**
1. (Optional) Create a venv  
   `python -m venv .venv && . .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
2. Install deps  
   `pip install -r requirements.txt`
3. Run  
   `python app/app.py`
4. Open `http://127.0.0.1:8080`  
   Health check: `http://127.0.0.1:8080/health`

---

### 2) Docker (Local Container)

**Files you need**
- `Dockerfile`
- `requirements.txt`
- `app/` (contains `app.py`, `templates/`, `static/`)
- `model.pkl`
- `schema.json`, `sample_request.json`

**Steps**
1. Build  
   `docker build -t loan-default-app .`
2. Run  
   `docker run -p 8080:8080 loan-default-app`
3. Open `http://127.0.0.1:8080`  
   Health check: `curl http://127.0.0.1:8080/health`

> Note: The container reads `MODEL_PATH=/app/model.pkl` (set in the Dockerfile). Keep `model.pkl` at repo root so `COPY model.pkl /app/model.pkl` works.

---

### 3) Heroku (Docker + GitHub CI/CD)

**Files you need**
- Everything from **Docker (Local)** plus:
- `.github/workflows/deploy.yml`  ← GitHub Actions workflow
- (Optional) `Procfile` if you ever build with the Python buildpack instead of Docker

**Required GitHub Repository Secrets**
- `HEROKU_API_KEY` (from Heroku Account → Applications → API Key)
- `HEROKU_APP_NAME` (e.g., `loan-default-stutteringemo`)
- `HEROKU_EMAIL` (your Heroku account email)
- *(If your workflow pushes to Docker Hub)* `DOCKER_USERNAME`, `DOCKER_PASSWORD`

**Steps**
1. Push to `main` (or the branch your workflow watches).  
2. GitHub Actions builds the Docker image and releases to Heroku.  
3. Open your app:  
   `https://<HEROKU_APP_NAME>.herokuapp.com`  
   Health check: `/health`

**Common gotchas**
- 404 on `/` usually means the app didn’t start or files aren’t where `app.py` expects. Ensure `templates/` and `static/` are under `app/`, and `model.pkl` + `schema.json` live at repo root.
- Heroku expects your web process to bind to `$PORT` (we already do via Gunicorn).

---

### 4) AWS SageMaker (Real-time Inference)

**Files you need**
- `model.tar.gz` containing:  
  - `model.pkl` at the archive root  
  - `code/inference.py` (SageMaker handler)  
  - `code/requirements.txt` (runtime deps for container)
- Notebook or script that:
  - uploads data to S3
  - uploads `model.tar.gz` to S3
  - creates a `sagemaker.sklearn.model.SKLearnModel` with your `ROLE_ARN`
  - deploys to an endpoint

**Prereqs**
- S3 bucket (e.g., `s3://<your-bucket>/loan-default/…`)  
- IAM role with SageMaker + S3 permissions (`ROLE_ARN`)  
- AWS creds configured in Studio Lab (or local): `aws configure` or environment variables

**Steps**
_To be completed after your endpoint stabilizes._  
(We’ll drop in the exact cells you ran: upload → model def → deploy → invoke → cleanup.)

---

### 5) Kubernetes (Optional)

**Files you need**
- `k8s/deployment.yaml` (or a combined manifest)
- A published Docker image (from Docker Hub or GHCR) that matches your app

**Steps**
1. Create a local cluster:
```bash
kind create cluster --name loan --image kindest/node:v1.32.2 --wait 180s
```
2. Build & load your image into the cluster:
```bash
docker build -t loan-default:latest .
kind load docker-image loan-default:latest --name loan
```

3. Apply the Kubernetes configuration:
```bash
kubectl apply -f k8s/loan-default.yaml
kubectl rollout status deploy/loan-default-api
```

4. Access the app:
```bash
# easiest for recording:
kubectl port-forward svc/loan-default-svc 8080:80
```
- Open in browser: http://localhost:8080     (health: /health, FastAPI docs: /docs)

5. Verify:
```bash
kubectl get pods -o wide
kubectl get svc loan-default-svc
curl http://localhost:8080/health
```

6. Cleanup:
```bash
kubectl delete -f k8s/loan-default.yaml
kind delete cluster --name loan
```

---
