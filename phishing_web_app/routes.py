"""
routes.py — Flask routes for the web application.
"""

import json
import os
import numpy as np
from pathlib import Path
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify

bp = Blueprint("main", __name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"
REPORT_DIR = BASE_DIR / "reports"

# ── Global model cache ────────────────────────────────────────────
_models = {}
_vectorizer = None
_text_vectorizer = None


def _load_models():
    """Lazy-load all models and vectorizer on first request."""
    global _models, _vectorizer, _text_vectorizer
    if _models:
        return

    import joblib

    from models.nn_model import NeuralNetModel
    from preprocess import load_text_vectorizer

    # TF-IDF vectorizer (used for Top Features explanation)
    vec_path = MODEL_DIR / "tfidf_vectorizer.pkl"
    if vec_path.exists():
        _vectorizer = joblib.load(vec_path)
        print("[OK] TF-IDF vectorizer loaded")

    # Keras Text Vectorizer
    if (MODEL_DIR / "text_vectorizer_vocab.json").exists():
        _text_vectorizer = load_text_vectorizer()
        print("[OK] Keras Text Vectorizer loaded")

    # Neural Network
    if (MODEL_DIR / "neural_network.keras").exists():
        _models["Neural Network"] = NeuralNetModel().load()

    print(f"[OK] Loaded models: {list(_models.keys())}")


@bp.route("/")
def home():
    _load_models()
    model_names = ["Rule-Based"] + list(_models.keys())
    return render_template("home.html", models=model_names)


@bp.route("/analyze", methods=["POST"])
def analyze():
    _load_models()

    subject = request.form.get("subject", "").strip()
    body = request.form.get("body", "").strip()
    sender = request.form.get("sender", "").strip()
    model_name = request.form.get("model", "Rule-Based")
    api_mode = request.form.get("api_mode", "false").lower() == "true"

    if not body:
        flash("Email body is required.", "danger")
        return redirect(url_for("main.home"))

    full_text = f"{subject} {body}"

    from preprocess import clean_text
    from rules import analyze_rules
    from explain import explain_prediction

    # Get prediction based on selected model
    is_phishing = False
    risk_score = 0

    if model_name == "Rule-Based":
        rule_result = analyze_rules(subject, body, sender)
        is_phishing = rule_result["is_phishing"]
        risk_score = rule_result["risk_score"]
    elif model_name == "Neural Network" and model_name in _models and _text_vectorizer is not None:
        X_seq = _text_vectorizer(np.array([full_text])).numpy()
        model = _models[model_name]
        pred = model.predict(X_seq)[0]
        proba = model.predict_proba(X_seq)[0]
        is_phishing = bool(pred == 1)
        risk_score = int(round(proba[1] * 100))
    else:
        flash(f"Model '{model_name}' is not available. Train models first.", "warning")
        return redirect(url_for("main.home"))

    # Generate explanation
    X_single = None
    if _vectorizer is not None:
        from preprocess import transform_text
        X_single = transform_text(_vectorizer, [full_text])

    explanation = explain_prediction(
        subject=subject,
        body=body,
        sender=sender,
        model_name=model_name,
        is_phishing=is_phishing,
        risk_score=risk_score,
        vectorizer=_vectorizer,
        X_single=X_single,
    )

    if is_phishing:
        try:
            from datetime import datetime
            log_path = BASE_DIR / "unsafe_logs.json"
            logs = []
            if log_path.exists():
                with open(log_path, "r") as f:
                    logs = json.load(f)
            logs.append({
                "id": str(len(logs) + 1),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "subject": subject,
                "sender": sender,
                "body_snippet": body[:300] + "..." if len(body) > 300 else body,
                "body": body,
                "model": model_name,
                "risk_score": risk_score,
                "explanation_text": explanation.get("explanation_text", "") if isinstance(explanation, dict) else "",
                "is_viewed": False
            })
            with open(log_path, "w") as f:
                json.dump(logs, f, indent=4)
        except Exception as e:
            print(f"[!] Failed to log unsafe email: {e}")

    if api_mode:
        from flask import jsonify
        return jsonify({
            "is_phishing": is_phishing,
            "risk_score": risk_score,
            "explanation": explanation
        })

    return render_template(
        "results.html",
        subject=subject,
        body=body,
        sender=sender,
        model_name=model_name,
        explanation=explanation,
    )


@bp.route("/analytics")
def analytics():
    results_path = MODEL_DIR / "evaluation_results.json"
    results = []
    if results_path.exists():
        with open(results_path) as f:
            results = json.load(f)
    return render_template("analytics.html", results=results)


@bp.route("/report")
def report():
    report_path = REPORT_DIR / "model_report.md"
    if report_path.exists():
        return send_file(str(report_path), as_attachment=True, download_name="model_report.md")
    flash("Report not generated yet. Run training first.", "warning")
    return redirect(url_for("main.analytics"))

@bp.route("/inbox-stats")
def inbox_stats():
    stats_path = BASE_DIR / "inbox_stats.json"
    if stats_path.exists():
        try:
            with open(stats_path) as f:
                return jsonify(json.load(f))
        except Exception:
            pass
    return jsonify({"analyzed": 0, "phishing": 0, "safe": 0, "running": False})

@bp.route("/threats")
def threats():
    log_path = BASE_DIR / "unsafe_logs.json"
    logs = []
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                logs = json.load(f)
        except Exception:
            pass
            
    # Backwards compatibility for old logs
    for i, log in enumerate(logs):
        if "id" not in log:
            log["id"] = str(i + 1)
            
    logs.reverse() # Show newest first
    return render_template("threats.html", logs=logs)

@bp.route("/threat/<log_id>")
def threat_detail(log_id):
    log_path = BASE_DIR / "unsafe_logs.json"
    logs = []
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                logs = json.load(f)
        except Exception:
            pass
            
    for i, log in enumerate(logs):
        current_id = log.get("id", str(i + 1))
        if str(current_id) == str(log_id):
            log["is_viewed"] = True
            try:
                with open(log_path, "w") as f:
                    json.dump(logs, f, indent=4)
            except Exception:
                pass
            return render_template("threat_detail.html", log=log)
            
    flash("Log entry not found.", "warning")
    return redirect(url_for("main.threats"))
