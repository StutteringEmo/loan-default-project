import os, joblib
from flask import Flask, request, jsonify
import pandas as pd

# Load the trained model from the project root
MODEL_PATH = os.environ.get("MODEL_PATH", "model.pkl")

artifact = joblib.load(MODEL_PATH)
pipe = artifact["pipeline"]

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}

@app.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(force=True)
    rows = payload if isinstance(payload, list) else [payload]
    df = pd.DataFrame(rows)
    proba = pipe.predict_proba(df)[:,1]
    pred = (proba >= 0.5).astype(int)
    return jsonify([
        {"prob_default": float(p), "pred_default": int(y)}
        for p, y in zip(proba, pred)
    ])

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))  # <-- use Heroku's dynamic port
    app.run(host="0.0.0.0", port=port)

