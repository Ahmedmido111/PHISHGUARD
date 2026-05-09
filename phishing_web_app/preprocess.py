"""
preprocess.py — Text cleaning and TF-IDF vectorization.
"""

import re
import joblib
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)


def clean_text(text: str) -> str:
    """Clean email text for model consumption."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Strip URLs
    text = re.sub(r"https?://\S+|www\.\S+", " URL ", text)
    # Strip email addresses
    text = re.sub(r"\S+@\S+", " EMAIL ", text)
    # Keep only letters, digits, spaces
    text = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF\s]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_tfidf(texts, max_features: int = 5000, save: bool = True):
    """Build and fit TF-IDF vectorizer."""
    cleaned = [clean_text(t) for t in texts]
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.95,
    )
    X = vectorizer.fit_transform(cleaned)
    if save:
        joblib.dump(vectorizer, MODEL_DIR / "tfidf_vectorizer.pkl")
        print(f"[OK] TF-IDF vectorizer saved ({X.shape[1]} features)")
    return vectorizer, X


def load_tfidf():
    """Load a previously saved TF-IDF vectorizer."""
    path = MODEL_DIR / "tfidf_vectorizer.pkl"
    return joblib.load(path)


def transform_text(vectorizer, texts):
    """Transform texts using an already-fitted vectorizer."""
    cleaned = [clean_text(t) for t in texts]
    return vectorizer.transform(cleaned)


def split_data(X, y, test_size: float = 0.2, random_state: int = 42):
    """Train/test split."""
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def build_text_vectorizer(texts, max_tokens: int = 15000, sequence_length: int = 300):
    """Build and adapt a Keras TextVectorization layer."""
    from tensorflow.keras.layers import TextVectorization
    
    vectorizer = TextVectorization(
        max_tokens=max_tokens,
        output_mode='int',
        output_sequence_length=sequence_length,
        standardize=None  # We use our own clean_text
    )
    
    cleaned = [clean_text(t) for t in texts]
    vectorizer.adapt(cleaned)
    
    # Save the vocabulary
    import json
    vocab = vectorizer.get_vocabulary()
    with open(MODEL_DIR / "text_vectorizer_vocab.json", "w", encoding="utf-8") as f:
        json.dump(vocab, f)
        
    print(f"[OK] TextVectorization adapted ({len(vocab)} tokens) and vocabulary saved")
    return vectorizer


def load_text_vectorizer(max_tokens: int = 15000, sequence_length: int = 300):
    """Reconstruct TextVectorization from saved vocab."""
    import json
    from tensorflow.keras.layers import TextVectorization
    
    vocab_path = MODEL_DIR / "text_vectorizer_vocab.json"
    vectorizer = TextVectorization(
        max_tokens=max_tokens,
        output_mode='int',
        output_sequence_length=sequence_length,
        standardize=None
    )
    
    if vocab_path.exists():
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab = json.load(f)
        vectorizer.set_vocabulary(vocab)
    else:
        # Fallback dummy vocab if not found
        vectorizer.set_vocabulary(["", "[UNK]"])
        
    return vectorizer
