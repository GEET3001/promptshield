"""Shared scoring function used by baselines, fine-tuning and evaluation."""
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score


def _f1_subset(y_true, y_pred, mask):
    if mask.sum() == 0:
        return float("nan")
    return round(float(f1_score(y_true[mask], y_pred[mask], zero_division=0)), 4)


def score(y_true, y_pred, languages) -> dict:
    """Overall metrics plus F1 on English and on Hindi/Hinglish rows. fpr = false-positive rate."""
    y_true, y_pred, languages = np.asarray(y_true), np.asarray(y_pred), np.asarray(languages)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "fpr": round(float(fp / (fp + tn)) if (fp + tn) else 0.0, 4),
        "f1_en": _f1_subset(y_true, y_pred, languages == "en"),
        "f1_hi_hinglish": _f1_subset(y_true, y_pred, np.isin(languages, ["hi", "hinglish"])),
    }
