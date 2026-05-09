"""
evaluation.py — Compare all approaches with classification metrics.
"""

import json
import numpy as np
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"


def evaluate_model(name: str, y_true, y_pred) -> dict:
    """Compute metrics for a single model."""
    return {
        "model": name,
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def evaluate_all(y_true, predictions: dict) -> list:
    """
    Evaluate all models.

    Args:
        y_true: ground-truth labels (0/1)
        predictions: dict of {model_name: y_pred_array}

    Returns:
        List of result dicts, also saved to JSON.
    """
    results = []
    for name, y_pred in predictions.items():
        res = evaluate_model(name, y_true, y_pred)
        results.append(res)
        cm = res["confusion_matrix"]
        print(
            f"  {name:25s}  Acc={res['accuracy']:.4f}  "
            f"P={res['precision']:.4f}  R={res['recall']:.4f}  "
            f"F1={res['f1_score']:.4f}  CM={cm}"
        )

    # Save
    out_path = MODEL_DIR / "evaluation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[OK] Evaluation results saved to {out_path}")
    return results
