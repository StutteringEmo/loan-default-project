# app/app.py
import os
import json
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, request, jsonify, render_template

# -----------------------------
# Load model
# -----------------------------
MODEL_PATH = os.environ.get("MODEL_PATH", "model.pkl")
artifact = joblib.load(MODEL_PATH)
pipe = artifact["pipeline"]

# -----------------------------
# Flask
# -----------------------------
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent      # .../app
ROOT_DIR = BASE_DIR.parent                      # project root


def _load_json_anywhere(filename: str):
    """Try root first, then app/; return None if not found/invalid."""
    for p in (ROOT_DIR / filename, BASE_DIR / filename):
        try:
            if p.exists():
                with p.open("r", encoding="utf-8-sig") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load {filename} from {p}: {e}")
    return None


# -----------------------------
# Expected columns in your model
# (from the earlier sklearn error trace)
# -----------------------------
EXPECTED_COLS = [
    "Age",
    "CreditScore",
    "Education",
    "MonthsEmployed",
    "NumCreditLines",
    "DTIRatio",
    "InterestRate",
    "HasMortgage",
    "MaritalStatus",
    "LoanPurpose",
    "Income",
    "LoanTerm",
    "EmploymentType",
    "HasCoSigner",
    "HasDependents",
    "LoanAmount",
]

# Map UI 'purpose' -> model "LoanPurpose" categories (adjust if your model uses different names)
PURPOSE_MAP = {
    "debt_consolidation": "Debt Consolidation",
    "home_improvement": "Home Improvement",
    "medical": "Medical",
    "major_purchase": "Major Purchase",
    "small_business": "Small Business",
    "vacation": "Vacation",
    "other": "Other",
}


def build_feature_row(ui: dict) -> pd.DataFrame:
    """
    Build ONE model-ready row from the small UI payload.
    Any columns not supplied by the UI are filled with reasonable defaults.
    """
    # Coerce/clean UI inputs
    age = _to_number(ui.get("age"))
    income = _to_number(ui.get("income"))                  # assume monthly income
    dti = _to_number(ui.get("debt_ratio"))
    num_lines = _to_number(ui.get("open_credit_lines"))
    past_due = _to_number(ui.get("past_due_30_59"))
    loan_amt = _to_number(ui.get("loan_amount"))
    purpose_raw = (ui.get("purpose") or "").strip().lower()
    loan_purpose = PURPOSE_MAP.get(purpose_raw, "Other")

    # Defaults for features your pipeline expects but UI doesn’t collect
    row = {
        "Age": age if age is not None else 0,
        "CreditScore": 650,                 # default/median-ish, adjust to your dataset
        "Education": "unknown",
        "MonthsEmployed": 24,               # 2 years by default
        "NumCreditLines": num_lines if num_lines is not None else 0,
        "DTIRatio": dti if dti is not None else 0.0,
        "InterestRate": 12.0,               # if your model had this; otherwise it will be ignored
        "HasMortgage": 0,
        "MaritalStatus": "unknown",
        "LoanPurpose": loan_purpose,
        "Income": income if income is not None else 0.0,   # monthly
        "LoanTerm": 36,                     # months, adjust to your dataset
        "EmploymentType": "unknown",
        "HasCoSigner": 0,
        "HasDependents": 0,
        "LoanAmount": loan_amt if loan_amt is not None else 0.0,
    }

    # If your model actually uses any “past-due” feature, you can map it here:
    # e.g., row["PastDue_30_59"] = past_due if past_due is not None else 0

    # Reorder to EXACT column order (not strictly required by sklearn, but nice for logging)
    row_ordered = {c: row.get(c) for c in EXPECTED_COLS}
    df = pd.DataFrame([row_ordered], columns=EXPECTED_COLS)

    print("[DEBUG] Model input columns:", list(df.columns))
    print("[DEBUG] Model input row:\n", df.to_string(index=False))
    return df


def _to_number(x):
    try:
        if x is None or x == "":
            return None
        return float(x)
    except Exception:
        return None


# -----------------------------
# Routes
# -----------------------------
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


@app.route("/", methods=["GET"])
def home():
    schema = _load_json_anywhere("schema.json")
    sample = _load_json_anywhere("sample_request.json") or {}
    # Accept a JSON Schema (with "properties") or a flat mapping
    if isinstance(schema, dict) and isinstance(schema.get("properties"), dict):
        properties = schema["properties"]
    elif isinstance(schema, dict):
        properties = schema
    else:
        properties = {}
    fields = list(properties.keys())
    if properties:
        print(f"[OK] Rendering form with {len(fields)} fields")
    else:
        print("[OK] Rendering raw JSON mode")
    return render_template(
        "index.html",
        properties=properties,
        fields=fields,
        sample_json=json.dumps(sample, indent=2),
    )


@app.route("/predict", methods=["POST"])
def predict():
    payload = request.get_json(force=True)
    rows = payload if isinstance(payload, list) else [payload]

    # Build a DF the pipeline recognizes
    X = pd.concat([build_feature_row(r) for r in rows], ignore_index=True)

    # Predict
    proba = pipe.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)

    out = [{"prob_default": float(p), "pred_default": int(y)} for p, y in zip(proba, pred)]
    return jsonify(out if len(out) > 1 else out[0])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
