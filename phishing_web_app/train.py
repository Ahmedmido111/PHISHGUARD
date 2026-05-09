"""
train.py — End-to-end training pipeline.

Usage:
    python train.py
"""

import sys
import numpy as np
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_loader import load_and_merge
from preprocess import build_tfidf, split_data, clean_text

from models.nn_model import NeuralNetModel
from evaluation import evaluate_all
from rules import analyze_rules
from report import generate_report


def main():
    print("=" * 60)
    print("  PHISHING EMAIL DETECTOR — Training Pipeline")
    print("=" * 60)

    # 1. Load data
    print("\n[1/6] Loading and merging datasets...")
    df = load_and_merge(max_samples=60000)

    # 2. Preprocess
    print("\n[2/6] Building TF-IDF features and Text Vectorizer...")
    from preprocess import build_text_vectorizer
    
    # Truncate texts to max 10000 chars to prevent numpy string array OOM on base64 dumps
    truncated_texts = df["text"].str.slice(0, 5000).tolist()
    
    vectorizer, X_tfidf = build_tfidf(truncated_texts)
    text_vectorizer = build_text_vectorizer(truncated_texts)
    
    # Generate integer sequences for NN in batches
    print("  Vectorizing text to integer sequences...")
    X_seq_list = []
    batch_size = 2000
    for i in range(0, len(truncated_texts), batch_size):
        batch = truncated_texts[i:i+batch_size]
        X_seq_list.append(text_vectorizer(batch).numpy())
    X_seq = np.vstack(X_seq_list)
    
    y = (df["label"] == "phishing").astype(int).values

    # 3. Split
    print("\n[3/6] Splitting train/test...")
    from sklearn.model_selection import train_test_split
    indices = np.arange(len(df))
    train_idx, test_idx = train_test_split(indices, test_size=0.2, random_state=42, stratify=y)
    
    y_train, y_test = y[train_idx], y[test_idx]
    X_seq_train, X_seq_test = X_seq[train_idx], X_seq[test_idx]
    print(f"  Train: {len(y_train)}  |  Test: {len(y_test)}")

    # 4. Train models
    print("\n[4/6] Training models...")



    nn = NeuralNetModel(sequence_length=X_seq_train.shape[1], vocab_size=15000, embedding_dim=64)
    nn.train(X_seq_train, y_train, epochs=8, batch_size=256)
    nn.save()

    # 5. Evaluate
    print("\n[5/6] Evaluating all models...")
    # Build rule-based predictions on test set
    test_texts = df.iloc[y_test.shape[0] * -1:]["text"].tolist() if len(df) > 0 else []
    # Recompute from the original df using the test indices
    # We need the original texts for rule-based eval
    all_texts = df["text"].tolist()
    # Get test indices — we used sklearn split which shuffles, so we need to re-derive
    from sklearn.model_selection import train_test_split
    _, test_idx = train_test_split(
        range(len(all_texts)), test_size=0.2, random_state=42, stratify=y
    )
    test_texts_for_rules = [all_texts[i] for i in test_idx]

    rule_preds = []
    for text in test_texts_for_rules:
        result = analyze_rules("", text, "")
        rule_preds.append(1 if result["is_phishing"] else 0)
    rule_preds = np.array(rule_preds)

    predictions = {
        "Rule-Based": rule_preds,
        "Neural Network": nn.predict(X_seq_test),
    }

    results = evaluate_all(y_test, predictions)

    # 6. Generate report
    print("\n[6/6] Generating report...")
    generate_report(results)

    print("\n" + "=" * 60)
    print("  Training complete! All models and report saved.")
    print("=" * 60)


if __name__ == "__main__":
    main()
