"""
imap_monitor.py — Background daemon to monitor an IMAP inbox for phishing emails.

Config parameters are loaded from `imap_config.json`.
Usage:
    python imap_monitor.py
"""

import sys
import json
import time
import email
from email.header import decode_header
import imaplib
import requests
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "imap_config.json"
STATS_PATH  = BASE_DIR / "inbox_stats.json"       # shared stats file
FLASK_URL   = "http://127.0.0.1:5000/analyze"

def load_config():
    if not CONFIG_PATH.exists():
        default_config = {
            "EMAIL_ACCOUNT": "ADD Email Account for monitoring",
            "APP_PASSWORD": "your-app-password-here",
            "IMAP_SERVER": "outlook.office365.com",
            "IMAP_PORT": 993,
            "PREFERRED_MODEL": "Neural Network",
            "POLL_INTERVAL_SECONDS": 15,
            "MONITORED_FOLDERS": ["INBOX", "Junk Email", "[Gmail]/Spam"]
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(default_config, f, indent=4)
        print(f"[!] Warning: Config file created at {CONFIG_PATH}")
        print("Please edit the config file with your App Password before running.")
        sys.exit(1)
        
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

# ── Shared stats helpers ──────────────────────────────────────────────────────

def _load_stats() -> dict:
    if STATS_PATH.exists():
        try:
            with open(STATS_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {"analyzed": 0, "phishing": 0, "safe": 0, "running": False}

def _save_stats(stats: dict):
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)

def _increment(field: str):
    stats = _load_stats()
    stats[field] = stats.get(field, 0) + 1
    _save_stats(stats)

# ── Header / body helpers ─────────────────────────────────────────────────────

def clean_header(header_value):
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    result = ""
    for frag, enc in decoded_fragments:
        if isinstance(frag, bytes):
            result += frag.decode(enc or 'utf-8', errors='ignore')
        else:
            result += str(frag)
    return result

def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        return msg.get_payload(decode=True).decode('utf-8', errors='ignore')
    return ""

def pop_notification(title, message, urgency="normal"):
    """Shows a desktop notification via notify-send on Linux."""
    try:
        subprocess.run(["notify-send", "-u", urgency, "-a", "PhishGuard Auto-Alert", title, message], check=False)
    except Exception as e:
        print(f"[!] Failed to send notification: {e}")

# ── Main monitor ──────────────────────────────────────────────────────────────

def run_monitor():
    cfg = load_config()
    print("-" * 60)
    print("  PHISHGUARD Inbox Monitor")
    print("-" * 60)
    print(f"[*] Account: {cfg['EMAIL_ACCOUNT']}")
    print(f"[*] Server:  {cfg['IMAP_SERVER']}:{cfg['IMAP_PORT']}")
    print(f"[*] Model:   {cfg['PREFERRED_MODEL']}")
    
    try:
        mail = imaplib.IMAP4_SSL(cfg["IMAP_SERVER"], cfg["IMAP_PORT"])
        mail.login(cfg["EMAIL_ACCOUNT"], cfg["APP_PASSWORD"])
        print("[OK] Login successful. Listening for new emails across configured folders...")
    except Exception as e:
        print(f"[X] IMAP login failed: {e}")
        print("Make sure you provide the correct App Password and IMAP server in imap_config.json")
        sys.exit(1)

    # Mark monitor as running
    stats = _load_stats()
    stats["running"] = True
    _save_stats(stats)

    processed_uids = set()

    monitored_folders = cfg.get("MONITORED_FOLDERS", ["INBOX", "Junk Email", "[Gmail]/Spam"])

    # ── Seed: skip ALL emails currently in monitored folders (read + unread) ─────────────
    try:
        total_skipped = 0
        for folder in monitored_folders:
            try:
                status, _ = mail.select(folder, readonly=True)
                if status == "OK":
                    s_search, all_msgs = mail.uid('search', 'ALL')
                    if s_search == "OK" and all_msgs[0]:
                        uids = all_msgs[0].split()
                        for uid in uids:
                            processed_uids.add(f"{folder}:{uid.decode('utf-8')}")
                        total_skipped += len(uids)
                        print(f"[*] Skipped {len(uids)} existing emails in {folder}.")
            except Exception:
                pass
        print(f"[*] Total skipped: {total_skipped} emails. Only NEW arrivals will be analyzed.")
    except Exception as e:
        print(f"[!] Error seeding existing emails: {e}")

    try:
        while True:
            try:
                # Force refresh connection state
                mail.noop()
                
                for folder in monitored_folders:
                    try:
                        status, _ = mail.select(folder, readonly=True)
                        if status != "OK":
                            continue
                    except Exception:
                        continue
                        
                    status, messages = mail.uid('search', 'ALL')
                    
                    if status == "OK" and messages[0]:
                        for uid in messages[0].split():
                            uid_key = f"{folder}:{uid.decode('utf-8')}"
                            if uid_key in processed_uids:
                                continue
                            
                            processed_uids.add(uid_key)
                            status2, msg_data = mail.uid('fetch', uid, '(BODY.PEEK[])')
                            
                            for response_part in msg_data:
                                if isinstance(response_part, tuple):
                                    msg = email.message_from_bytes(response_part[1])
                                    
                                    subject = clean_header(msg["Subject"])
                                    sender = clean_header(msg["From"])
                                    body = get_body(msg)
                                    
                                    print(f"\n[RECEIVED] {subject} (from: {sender})")
                                    
                                    # Send to Flask app for inference
                                    print("  [*] Synthesizing with Flask detector...")
                                    try:
                                        resp = requests.post(FLASK_URL, data={
                                            "subject": subject,
                                            "sender": sender,
                                            "body": body,
                                            "model": cfg["PREFERRED_MODEL"],
                                            "api_mode": "true"
                                        }, timeout=30)
                                        
                                        result = resp.json()
                                        is_phishing = result.get("is_phishing", False)
                                        explanation = result.get("explanation", {})
                                        explanation_text = explanation.get("explanation_text", "No detailed explanation provided.")
                                        
                                        # Update shared stats
                                        _increment("analyzed")
                                        
                                        if is_phishing:
                                            _increment("phishing")
                                            title = "🚨 PHISHING ALERT"
                                            msg_text = f"Email: '{subject}'\nClassification: PHISHING\nReason: {explanation_text}\n\nPlease review the PhishGuard dashboard."
                                            print("  [X] DETECTED AS PHISHING!")
                                            pop_notification(title, msg_text, urgency="critical")
                                        else:
                                            _increment("safe")
                                            title = "✅ Safe Email"
                                            msg_text = f"Email: '{subject}'\nStatus: SAFE\nReason: {explanation_text}"
                                            print("  [OK] Email is safe.")
                                            pop_notification(title, msg_text, urgency="normal")
                                            
                                    except Exception as req_err:
                                        print(f"  [!] Error calling Flask: {req_err}")
                        
                # Heartbeat sleep
                time.sleep(cfg["POLL_INTERVAL_SECONDS"])
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"[!] Error during fetch cycle: {e}")
                time.sleep(10)

    except KeyboardInterrupt:
        print("\n[-] Monitor stopped.")
    finally:
        stats = _load_stats()
        stats["running"] = False
        _save_stats(stats)

if __name__ == "__main__":
    run_monitor()
