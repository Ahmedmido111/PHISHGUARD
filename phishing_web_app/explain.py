"""
explain.py — Explanation engine for predictions.
"""

import numpy as np
from typing import Dict, List, Tuple
from rules import analyze_rules


def get_top_tfidf_features(vectorizer, X_single, top_n: int = 10) -> List[Tuple[str, float]]:
    """Return the top TF-IDF features for a single sample."""
    feature_names = vectorizer.get_feature_names_out()
    row = X_single.toarray().flatten() if hasattr(X_single, "toarray") else np.asarray(X_single).flatten()
    top_idx = row.argsort()[-top_n:][::-1]
    return [(feature_names[i], round(float(row[i]), 4)) for i in top_idx if row[i] > 0]


def highlight_suspicious(body: str, phrases: List[str]) -> str:
    """Wrap suspicious phrases in <mark> tags for HTML display."""
    highlighted = body
    for phrase in phrases:
        if phrase.lower() in highlighted.lower():
            import re
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            highlighted = pattern.sub(f"<mark>{phrase}</mark>", highlighted)
    return highlighted


def explain_prediction(
    subject: str,
    body: str,
    sender: str,
    model_name: str,
    is_phishing: bool,
    risk_score: float,
    vectorizer=None,
    X_single=None,
) -> Dict:
    """
    Generate a full explanation for a single prediction.

    Returns:
        {
            "classification": str,
            "risk_score": int,
            "top_features": [(word, weight), ...],
            "triggered_rules": [str],
            "suspicious_phrases": [str],
            "highlighted_body": str,
            "explanation_text": str,
        }
    """
    # Rule analysis
    rule_result = analyze_rules(subject, body, sender)
    triggered_rules = rule_result["triggered_rules"]
    suspicious_phrases = rule_result["suspicious_phrases"]

    # Top TF-IDF features
    top_features = []
    if vectorizer is not None and X_single is not None:
        top_features = get_top_tfidf_features(vectorizer, X_single)
        # add top feature words to suspicious phrases
        feature_words = [w for w, _ in top_features[:5]]
        suspicious_phrases.extend(feature_words)

    suspicious_phrases = list(set(suspicious_phrases))

    # Highlighted body
    highlighted_body = highlight_suspicious(body, suspicious_phrases)

    # Human-readable explanation
    classification = "Phishing" if is_phishing else "Safe"
    parts = []
    if is_phishing:
        parts.append(f"This email is classified as **{classification}** by the {model_name} model with a risk score of {risk_score}/100.")
        if triggered_rules:
            parts.append("Triggered rules: " + "; ".join(triggered_rules[:5]) + ".")
        if top_features:
            words = ", ".join([f'"{w}"' for w, _ in top_features[:5]])
            parts.append(f"Key features: {words}.")
    else:
        parts.append(f"This email appears to be **{classification}** according to the {model_name} model (risk score: {risk_score}/100).")
        parts.append("No major phishing indicators detected.")

    # Internal Mechanics details
    internal_mechanics_explanation = ""
    if model_name == "Rule-Based":
        internal_mechanics_explanation = (
            "<strong>Internal Mechanics:</strong> The Rule-Based system is a deterministic model. "
            "It searches for explicitly defined patterns (e.g., regex for IP-based URLs) and localized keywords "
            "('urgent', 'verify account'). It applies a weighted sum to all triggered rules "
            "to arrive at the final risk score. Its goal is reached by direct pattern matching rather than statistical correlation."
        )
    elif model_name == "Neural Network":
        internal_mechanics_explanation = (
            "<strong>Internal Mechanics:</strong> The Neural Network is a deep-learning classification model. "
            "It transforms the email text into a 5,000-dimensional TF-IDF vector, representing the statistical frequency "
            "of key terms. This vector passes through hidden Dense layers using ReLU activation functions to learn complex "
            "non-linear interactions between words. The final output node uses a Sigmoid function to squash the logic into "
            "a probability risk score between 0 and 100%. Its goal is reached by combining thousands of learned lexical weights."
        )

    return {
        "classification": classification,
        "risk_score": int(risk_score),
        "top_features": top_features,
        "triggered_rules": triggered_rules,
        "suspicious_phrases": suspicious_phrases,
        "highlighted_body": highlighted_body,
        "explanation_text": " ".join(parts),
        "internal_mechanics": internal_mechanics_explanation,
    }
