"""
nn_model.py — Keras Dense neural network for phishing detection.
"""

import os
import numpy as np
from pathlib import Path
from scipy import sparse

# Suppress TF logging
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "saved_models"
MODEL_DIR.mkdir(exist_ok=True)


class NeuralNetModel:
    """Simple Keras Dense network for binary phishing classification."""

    def __init__(self, sequence_length: int = 300, vocab_size: int = 15000, embedding_dim: int = 64):
        self.sequence_length = sequence_length
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.model = None
        self.name = "Neural Network"

    def _build(self):
        import tensorflow as tf
        tf.get_logger().setLevel("ERROR")
        from tensorflow import keras
        from tensorflow.keras import layers

        model = keras.Sequential([
            layers.Input(shape=(self.sequence_length,)),
            layers.Embedding(input_dim=self.vocab_size, output_dim=self.embedding_dim),
            layers.GlobalAveragePooling1D(),
            layers.Dense(128, activation="relu"),
            layers.Dropout(0.3),
            layers.Dense(64, activation="relu"),
            layers.Dropout(0.3),
            layers.Dense(1, activation="sigmoid"),
        ])
        model.compile(
            optimizer="adam",
            loss="binary_crossentropy",
            metrics=["accuracy"],
        )
        self.model = model

    def _to_dense(self, X):
        if sparse.issparse(X):
            return X.toarray()
        return np.asarray(X)

    def train(self, X_train, y_train, epochs: int = 5, batch_size: int = 256):
        # Determine sequence_length from input if passed a numpy array
        self.sequence_length = X_train.shape[1]
        y_train = np.asarray(y_train).astype(np.float32)
        self._build()
        self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.1,
            verbose=1,
        )
        print(f"[OK] {self.name} trained")

    def predict(self, X):
        probs = self.model.predict(X, verbose=0).flatten()
        return (probs >= 0.5).astype(int)

    def predict_proba(self, X):
        phish_prob = self.model.predict(X, verbose=0).flatten()
        safe_prob = 1 - phish_prob
        return np.column_stack([safe_prob, phish_prob])

    def save(self):
        path = MODEL_DIR / "neural_network.keras"
        self.model.save(str(path))
        print(f"[OK] {self.name} saved to {path}")

    def load(self):
        import tensorflow as tf
        tf.get_logger().setLevel("ERROR")
        from tensorflow import keras

        path = MODEL_DIR / "neural_network.keras"
        self.model = keras.models.load_model(str(path))
        self.sequence_length = self.model.input_shape[-1]
        print(f"[OK] {self.name} loaded from {path}")
        return self
