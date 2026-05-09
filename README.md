# PhishGuard — Phishing Email Detector

<p align="center">
  A smart, Flask-based web application designed to identify and explain phishing emails using a dual-method approach: a deep learning Neural Network and a classical rule-based analysis system.
</p>

## ✨ Features

- **Dual-Model Inference:** Compares predictions from a trained Keras Neural Network with a structured rule-based system.
- **Deep Explanations:** Explanations for why an email was classified as phishing to build user trust.
- **Analytics Dashboard:** Graphical comparison of model accuracy, F1-scores, and false positive rates.
- **Automated IMAP Monitoring:** A background daemon (`imap_monitor.py`) watches over your Inbox and Junk folders, actively scanning new inbound emails.
- **Desktop Notifications:** Real-time system desktop popups when a malicious email is detected via the IMAP monitor.

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- An email account with App Passwords enabled (for IMAP monitoring)

### 2. Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/phishing_web_app.git
cd phishing_web_app/phishing_web_app

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Training the Models

Before running the app, you need to train the neural network and generate the rule-based thresholds.

```bash
python train.py
```
This script will:
- Load, merge, and clean the included SpamAssassin and CSV datasets.
- Train the Neural Network model.
- Generate and save evaluation metrics.
- Produce a comparison Markdown report in the `reports/` folder.

### 4. Running the Web App

Start the Flask web server:

```bash
export FLASK_APP=app.py  # On Windows CMD: set FLASK_APP=app.py or PowerShell: $env:FLASK_APP="app.py"
flask run
```

Then, open your web browser and navigate to [http://localhost:5000](http://localhost:5000).

## 📡 Automated IMAP Monitoring

PhishGuard provides a background daemon (`imap_monitor.py`) for continuous monitoring. It surveys your Inbox and Junk/Spam folders ("Junk Email", "[Gmail]/Spam") for newly received suspicious emails.

### Configuration
1. Rename or create `imap_config.json` with your email details.
2. Provide your IMAP server address, email, and **App Password** (do not use your regular password).
3. Set your `PREFERRED_MODEL` to either `nn` (Neural Network) or `rule`.

### Starting the Monitor
In a separate terminal window, ensure the Flask app is running, then execute:
```bash
python imap_monitor.py
```
When a new email is encountered, it is automatically forwarded to the local Flask `/analyze` endpoint securely. If flagged, you'll receive a native desktop notification!

## 🗺️ Project Structure

```text
phishing_web_app/
├── app.py              # Flask entry point
├── routes.py           # API and frontend URL routes
├── data_loader.py      # Dataset extraction & parsing
├── preprocess.py       # Text cleaning & TF-IDF vectorization
├── rules.py            # Rule-based detection algorithms
├── explain.py          # Explanation engine for flag reasoning
├── evaluation.py       # Model evaluation and metrics creation
├── report.py           # Automated report generation
├── train.py            # Complete training pipeline
├── imap_monitor.py     # Background IMAP scanning daemon
├── imap_config.json    # IMAP credentials and settings
├── models/
│   └── nn_model.py     # Keras Dense network architecture
├── templates/          # Jinja2 HTML templates
├── static/             # CSS styling and static assets
├── data/               # Raw Ham/Spam datasets
├── saved_models/       # Serialized models and TF-IDF vocab
└── reports/            # Auto-generated analytical reports
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to check [issues page](https://github.com/Ahmedmido111/phishing_web_app/issues).

## 📝 License

This project is open-source and available under the [MIT License](LICENSE).


