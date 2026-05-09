"""
rules.py — Rule-based phishing detection engine.
"""

import re
from typing import Dict, List, Tuple


# ── Keyword dictionaries ──────────────────────────────────────────

URGENT_WORDS = [
    "urgent", "immediately", "asap", "right away", "act now",
    "respond immediately", "time sensitive", "expires today",
    "deadline", "warning", "alert", "critical",
    # Arabic urgency keywords
    "عاجل", "فوري", "فورا", "تحذير", "خطير", "انتبه",
    "هام جدا", "مهم", "عاجل جدا", "تنبيه", "تنبيه أمني",
    "مطلوب فورا", "يرجى الرد", "خلال 24 ساعة",
]

PHISHING_KEYWORDS = [
    "verify your account", "confirm your identity", "click here",
    "update your information", "suspended", "unusual activity",
    "unauthorized", "security alert", "verify your email",
    "your account has been", "limited time", "free gift",
    "you have won", "claim your prize", "lottery",
    "congratulations", "account will be closed",
    "reset your password", "confirm your password",
    "dear customer", "dear user", "valued customer",
    "social security", "credit card number", "bank account",
    "wire transfer", "western union", "bitcoin",
    "nigerian prince", "inheritance",
    # Arabic phishing keywords
    "تحقق من حسابك", "تأكيد الهوية", "اضغط هنا",
    "حسابك معلق", "نشاط مشبوه", "تحديث بياناتك",
    "انقر هنا", "انقر الرابط", "الرجاء التحديث",
    "تحديث الحساب", "ايقاف الحساب", "تجميد حسابك",
    "يرجى التحقق", "فزت بجائزة", "ربحت", "الفائز",
    "تحديث فوري", "تأكيد حسابك", "بطاقة ائتمان",
    "الرقم السري", "كلمة المرور", "تسجيل الدخول",
    "تأكيد الدفع", "حساب بنكي", "تحديث أمني",
    "يرجى تأكيد", "حظر حسابك", "سيتم ايقاف",
]

SUSPICIOUS_LINK_PATTERNS = [
    r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",  # IP-based URLs
    r"https?://bit\.ly/",     # Shortened
    r"https?://tinyurl\.com/",
    r"https?://goo\.gl/",
    r"https?://t\.co/",
    r"https?://ow\.ly/",
    r"https?://is\.gd/",
    r"https?://[^/]*login[^/]*\.",  # Fake login pages
    r"https?://[^/]*secure[^/]*\.",
    r"https?://[^/]*verify[^/]*\.",
    r"https?://[^/]*update[^/]*\.",
    r"https?://[^/]*account[^/]*\.",
]

FREE_EMAIL_PROVIDERS = [
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "mail.com", "protonmail.com", "yandex.com",
    "zoho.com", "gmx.com",
]


def _check_urgent_words(text: str) -> List[str]:
    """Return list of matched urgent words."""
    text_lower = text.lower()
    return [w for w in URGENT_WORDS if w in text_lower]


def _check_phishing_keywords(text: str) -> List[str]:
    """Return list of matched phishing keywords."""
    text_lower = text.lower()
    return [k for k in PHISHING_KEYWORDS if k in text_lower]


def _check_suspicious_links(text: str) -> List[str]:
    """Return list of suspicious link matches."""
    found = []
    for pattern in SUSPICIOUS_LINK_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)
    return found


def _check_sender_anomaly(sender: str) -> List[str]:
    """Check sender/domain for anomalies."""
    issues = []
    if not sender:
        return issues
    sender = sender.lower().strip()
    # Free email used for "official" comms
    for provider in FREE_EMAIL_PROVIDERS:
        if provider in sender:
            issues.append(f"Sender uses free email provider ({provider})")
            break
    # Very long or obfuscated sender
    if len(sender) > 60:
        issues.append("Unusually long sender address")
    # Numeric heavy domain
    domain_part = sender.split("@")[-1] if "@" in sender else sender
    digit_ratio = sum(c.isdigit() for c in domain_part) / max(len(domain_part), 1)
    if digit_ratio > 0.4:
        issues.append("Domain contains many numbers (possible spoof)")
    return issues


def analyze_rules(subject: str, body: str, sender: str = "") -> Dict:
    """
    Run all rule-based checks and return results.

    Returns:
        {
            "is_phishing": bool,
            "risk_score": int (0-100),
            "triggered_rules": [str],
            "suspicious_phrases": [str],
        }
    """
    full_text = f"{subject} {body}"
    triggered = []
    suspicious_phrases = []
    score = 0

    # 1. Urgent words
    urgent = _check_urgent_words(full_text)
    if urgent:
        triggered.append(f"Urgent language detected: {', '.join(urgent[:5])}")
        suspicious_phrases.extend(urgent)
        score += min(len(urgent) * 8, 25)

    # 2. Phishing keywords
    keywords = _check_phishing_keywords(full_text)
    if keywords:
        triggered.append(f"Phishing keywords found: {', '.join(keywords[:5])}")
        suspicious_phrases.extend(keywords)
        score += min(len(keywords) * 10, 35)

    # 3. Suspicious links
    links = _check_suspicious_links(full_text)
    if links:
        triggered.append(f"Suspicious links detected: {len(links)} link(s)")
        suspicious_phrases.extend(links)
        score += min(len(links) * 15, 25)

    # 4. Sender anomaly
    sender_issues = _check_sender_anomaly(sender)
    if sender_issues:
        triggered.extend(sender_issues)
        score += min(len(sender_issues) * 8, 15)

    # Cap score
    score = min(score, 100)
    is_phishing = score >= 40

    return {
        "is_phishing": is_phishing,
        "risk_score": score,
        "triggered_rules": triggered,
        "suspicious_phrases": list(set(suspicious_phrases)),
    }
