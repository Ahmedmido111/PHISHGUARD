# Phishing Email Detection — Model Comparison Report

> Generated: 2026-05-07 00:01:46

---

## 1. Overview

This report compares two approaches for phishing email detection:

1. **Rule-Based System** — Pattern matching with urgency, phishing keywords, and suspicious link detection.
2. **Neural Network** — Keras Dense network with dropout regularization.

---

## 2. Evaluation Metrics

| Model | Accuracy | Precision | Recall | F1-Score |
|-------|----------|-----------|--------|----------|
| Rule-Based | 0.6127 | 0.8421 | 0.0046 | 0.0092 |
| Neural Network | 0.9233 | 0.8565 | 0.9642 | 0.9071 |

---

## 3. Confusion Matrices

### Rule-Based

```
  Predicted:  Safe  Phishing
  Actual Safe:   5437      3
  Actual Phish:  3444     16
```

### Neural Network

```
  Predicted:  Safe  Phishing
  Actual Safe:   4881    559
  Actual Phish:   124   3336
```

---

## 4. Pros and Cons

| Model | Pros | Cons |
|-------|------|------|
| Rule-Based | Fully interpretable; no training needed; works on small data | Requires manual maintenance; limited to known patterns |
| Neural Network | Learns complex patterns; highest potential accuracy; generalises to unseen patterns | Needs more data/compute; harder to interpret; risk of overfitting |
Needs more data/compute; harder to interpret; risk of overfitting |

---

## 5. Internal Mechanics Comparison

### How the Models Reach Their Goals

**Rule-Based System:**

- **Mechanism:** Deterministic pattern matching.

- **Process:** The system relies on handcrafted dictionaries and regular expressions. It computationally scans the raw strings for exact matches against a predefined list of threat vectors (e.g., 'urgent', 'click here', IP-based URLs). The resulting score is a simple weighted sum of these discrete matches.

- **Goal Reachiung:** It declares an email as 'Phishing' if the hardcoded threshold is crossed. This approach does not look at the context of words, only their explicit presence.


**Neural Network:**

- **Mechanism:** Statistical machine learning with non-linear mapping.

- **Process:** The system mathematically transforms the entire email corpus into a 5,000-dimensional mathematical vector (TF-IDF). This input vector propagates forward through multiple fully-connected hidden layers utilizing ReLU (Rectified Linear Unit) activations, allowing the network to synthesize subtle combinations of keywords that humans might miss.

- **Goal Reaching:** The final Dense node converts the extracted features using a Sigmoid activation into a continuous risk probability. It reaches its classification goal by weighting thousands of learned coefficients rather than explicit human-devised rules.


---

## 6. Sample Predictions

### Phishing Example

**Subject:** Urgent: Your Account Has Been Suspended

**Body:** Dear customer, click here immediately to verify your account or it will be permanently closed.

- Rule-Based → **Phishing** (urgent language + phishing keywords + suspicious action)

- Neural Network → **Phishing** (high TF-IDF weights on 'urgent', 'verify', 'suspended')


### Safe Example

**Subject:** Team meeting notes — April 2026

**Body:** Hi everyone, attached are the meeting notes from yesterday. Please review and let me know if I missed anything.

- Rule-Based → **Safe** (no triggers)

- Neural Network → **Safe** (low phishing probability)


---

## 6. Conclusion

The **Neural Network** achieves the highest F1-score of **0.9071**, making it the recommended model for production use. However, combining rule-based checks with ML models provides the most robust detection — rules catch known patterns while ML generalises to unseen phishing attempts.

---
*End of report*
