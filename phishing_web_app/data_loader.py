"""
data_loader.py — Extract, parse, label and merge SpamAssassin + CSV datasets.
"""

import os
import email
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def parse_raw_email(filepath: str) -> dict:
    """Parse a raw email file and return subject + body."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            msg = email.message_from_file(f)
        subject = msg.get("Subject", "") or ""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode("utf-8", errors="ignore")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="ignore")
        return {"subject": subject.strip(), "body": body.strip()}
    except Exception:
        return {"subject": "", "body": ""}


def load_spamassassin() -> pd.DataFrame:
    """Load and label SpamAssassin directories."""
    records = []
    label_map = {
        "easy_ham": "safe",
        "easy_ham_2": "safe",
        "hard_ham": "safe",
        "spam": "phishing",
        "spam_2": "phishing",
    }

    for dirname, label in label_map.items():
        dirpath = DATA_DIR / dirname
        if not dirpath.exists():
            print(f"  [SKIP] {dirpath} not found")
            continue
        files = [f for f in dirpath.iterdir() if f.is_file() and f.name != "cmds"]
        print(f"  Loading {dirname}: {len(files)} files → {label}")
        for fpath in files:
            parsed = parse_raw_email(str(fpath))
            text = (parsed["subject"] + " " + parsed["body"]).strip()
            if text:
                records.append({"text": text, "label": label})

    df = pd.DataFrame(records)
    print(f"  SpamAssassin total: {len(df)} emails")
    return df


def load_phishing_csv() -> pd.DataFrame:
    """Load the Phishing_Email.csv dataset."""
    csv_path = DATA_DIR / "Phishing_Email.csv"
    if not csv_path.exists():
        print(f"  [SKIP] {csv_path} not found")
        return pd.DataFrame(columns=["text", "label"])

    df = pd.read_csv(csv_path, usecols=["Email Text", "Email Type"])
    df = df.dropna(subset=["Email Text"])
    df = df.rename(columns={"Email Text": "text", "Email Type": "label"})
    # Normalise labels
    df["label"] = df["label"].str.strip().str.lower()
    df["label"] = df["label"].map(
        lambda x: "phishing" if x in ("phishing email", "phishing", "spam") else "safe"
    )
    print(f"  Phishing CSV total: {len(df)} emails")
    return df


def load_meajor_csv() -> pd.DataFrame:
    """Load the massive meajor_cleaned_preprocessed.csv dataset with sampling."""
    csv_path = BASE_DIR.parent / "meajor_cleaned_preprocessed.csv"
    if not csv_path.exists():
        print(f"  [SKIP] {csv_path} not found")
        return pd.DataFrame(columns=["text", "label"])

    try:
        # It's huge, so sample ~20000 rows
        df = pd.read_csv(csv_path, usecols=["subject", "body", "label"], encoding="utf-8")
        df = df.dropna(subset=["body"])
        df = df.sample(n=min(20000, len(df)), random_state=42)
        df["text"] = df["subject"].fillna("") + " " + df["body"]
        df["label"] = df["label"].map(lambda x: "phishing" if x == 1.0 or x == 1 else "safe")
        df = df[["text", "label"]]
        print(f"  Meajor CSV sampled total: {len(df)} emails")
        return df
    except Exception as e:
        print(f"  [ERROR] parsing Meajor CSV: {e}")
        return pd.DataFrame(columns=["text", "label"])


def load_arabic_xlsx() -> pd.DataFrame:
    """Load the Arabic Excel dataset."""
    xlsx_path = BASE_DIR.parent / "Arabic Phishing and Legitimate emails - Fully Dataset.xlsx"
    if not xlsx_path.exists():
        print(f"  [SKIP] {xlsx_path} not found")
        return pd.DataFrame(columns=["text", "label"])

    try:
        df = pd.read_excel(xlsx_path, usecols=["محتوى الإيميل", "نوع الإيميل"])
        df = df.rename(columns={"محتوى الإيميل": "text", "نوع الإيميل": "raw_label"})
        df = df.dropna(subset=["text", "raw_label"])
        df["label"] = df["raw_label"].astype(str).apply(
            lambda x: "phishing" if "Phish" in x else "safe"
        )
        df = df[["text", "label"]]
        print(f"  Arabic XLSX total: {len(df)} emails")
        return df
    except Exception as e:
        print(f"  [ERROR] parsing Arabic XLSX: {e}")
        return pd.DataFrame(columns=["text", "label"])


def load_and_merge(max_samples: int = 60000) -> pd.DataFrame:
    """Load all datasets, merge, shuffle, and optionally cap."""
    print("[*] Loading SpamAssassin data...")
    df_spam = load_spamassassin()
    print("[*] Loading Phishing CSV data...")
    df_csv = load_phishing_csv()
    print("[*] Loading Meajor CSV data...")
    df_meajor = load_meajor_csv()
    print("[*] Loading Arabic XLSX data...")
    df_arabic = load_arabic_xlsx()

    df = pd.concat([df_spam, df_csv, df_meajor, df_arabic], ignore_index=True)
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.len() > 10]
    df = df.drop_duplicates(subset=["text"])
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    if max_samples and len(df) > max_samples:
        # Balance the classes
        half = max_samples // 2
        safe = df[df["label"] == "safe"].head(half)
        phish = df[df["label"] == "phishing"].head(half)
        df = pd.concat([safe, phish], ignore_index=True).sample(
            frac=1, random_state=42
        ).reset_index(drop=True)

    merged_path = DATA_DIR / "merged_dataset.csv"
    df.to_csv(merged_path, index=False)
    print(f"[OK] Merged dataset: {len(df)} emails saved to {merged_path}")
    print(f"    Label distribution:\n{df['label'].value_counts().to_string()}")
    return df


if __name__ == "__main__":
    load_and_merge()
