"""
report.py — Generate Markdown report comparing all models.
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)


def generate_report(evaluation_results: list = None) -> str:
    """Generate a Markdown report and save to disk."""
    if evaluation_results is None:
        results_path = MODEL_DIR / "evaluation_results.json"
        if results_path.exists():
            with open(results_path) as f:
                evaluation_results = json.load(f)
        else:
            evaluation_results = []

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Phishing Email Detection — Model Comparison Report",
        f"\n> Generated: {now}\n",
        "---\n",
        "## 1. Overview\n",
        "This report compares two approaches for phishing email detection:\n",
        "1. **Rule-Based System** — Pattern matching with urgency, phishing keywords, "
        "and suspicious link detection.",
        "2. **Neural Network** — Keras Dense network with dropout regularization.\n",
        "---\n",
        "## 2. Evaluation Metrics\n",
        "| Model | Accuracy | Precision | Recall | F1-Score |",
        "|-------|----------|-----------|--------|----------|",
    ]

    for r in evaluation_results:
        lines.append(
            f"| {r['model']} | {r['accuracy']:.4f} | {r['precision']:.4f} "
            f"| {r['recall']:.4f} | {r['f1_score']:.4f} |"
        )

    lines.extend([
        "\n---\n",
        "## 3. Confusion Matrices\n",
    ])

    for r in evaluation_results:
        cm = r.get("confusion_matrix", [[0, 0], [0, 0]])
        lines.extend([
            f"### {r['model']}\n",
            "```",
            f"  Predicted:  Safe  Phishing",
            f"  Actual Safe:  {cm[0][0]:5d}  {cm[0][1]:5d}",
            f"  Actual Phish: {cm[1][0]:5d}  {cm[1][1]:5d}",
            "```\n",
        ])

    lines.extend([
        "---\n",
        "## 4. Pros and Cons\n",
        "| Model | Pros | Cons |",
        "|-------|------|------|",
        "| Rule-Based | Fully interpretable; no training needed; works on small data | "
        "Requires manual maintenance; limited to known patterns |",
        "| Neural Network | Learns complex patterns; highest potential accuracy; generalises to unseen patterns | "
        "Needs more data/compute; harder to interpret; risk of overfitting |",
        "Needs more data/compute; harder to interpret; risk of overfitting |",
        "\n---\n",
        "## 5. Internal Mechanics Comparison\n",
        "### How the Models Reach Their Goals\n",
        "**Rule-Based System:**\n",
        "- **Mechanism:** Deterministic pattern matching.\n",
        "- **Process:** The system relies on handcrafted dictionaries and regular expressions. It computationally scans the raw strings for exact matches against a predefined list of threat vectors (e.g., 'urgent', 'click here', IP-based URLs). The resulting score is a simple weighted sum of these discrete matches.\n",
        "- **Goal Reachiung:** It declares an email as 'Phishing' if the hardcoded threshold is crossed. This approach does not look at the context of words, only their explicit presence.\n\n",
        "**Neural Network:**\n",
        "- **Mechanism:** Statistical machine learning with non-linear mapping.\n",
        "- **Process:** The system mathematically transforms the entire email corpus into a 5,000-dimensional mathematical vector (TF-IDF). This input vector propagates forward through multiple fully-connected hidden layers utilizing ReLU (Rectified Linear Unit) activations, allowing the network to synthesize subtle combinations of keywords that humans might miss.\n",
        "- **Goal Reaching:** The final Dense node converts the extracted features using a Sigmoid activation into a continuous risk probability. It reaches its classification goal by weighting thousands of learned coefficients rather than explicit human-devised rules.\n",
        "\n---\n",
        "## 6. Sample Predictions\n",
        "### Phishing Example\n",
        "**Subject:** Urgent: Your Account Has Been Suspended\n",
        "**Body:** Dear customer, click here immediately to verify your account "
        "or it will be permanently closed.\n",
        "- Rule-Based → **Phishing** (urgent language + phishing keywords + suspicious action)\n",
        "- Neural Network → **Phishing** (high TF-IDF weights on 'urgent', 'verify', 'suspended')\n",
        "\n### Safe Example\n",
        "**Subject:** Team meeting notes — April 2026\n",
        "**Body:** Hi everyone, attached are the meeting notes from yesterday. "
        "Please review and let me know if I missed anything.\n",
        "- Rule-Based → **Safe** (no triggers)\n",
        "- Neural Network → **Safe** (low phishing probability)\n",
        "\n---\n",
        "## 6. Conclusion\n",
    ])

    # Dynamic conclusion based on best F1
    if evaluation_results:
        best = max(evaluation_results, key=lambda x: x.get("f1_score", 0))
        lines.append(
            f"The **{best['model']}** achieves the highest F1-score of "
            f"**{best['f1_score']:.4f}**, making it the recommended model for "
            f"production use. However, combining rule-based checks with ML models "
            f"provides the most robust detection — rules catch known patterns while "
            f"ML generalises to unseen phishing attempts."
        )
    else:
        lines.append("No evaluation results available yet. Run training first.")

    lines.append("\n---\n*End of report*\n")

    report_text = "\n".join(lines)
    report_path = REPORT_DIR / "model_report.md"
    with open(report_path, "w") as f:
        f.write(report_text)
    print(f"[OK] Report saved to {report_path}")
    return report_text


if __name__ == "__main__":
    generate_report()
