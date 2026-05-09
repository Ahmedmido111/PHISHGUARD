"""
app.py — Flask application entry point.
"""

import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "phishing-detector-secret-key-2026"

    # Register routes
    from routes import bp
    app.register_blueprint(bp)

    return app


if __name__ == "__main__":
    app = create_app()
    print("[*] Starting Phishing Email Detector on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
