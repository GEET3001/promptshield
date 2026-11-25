"""Layer 3: fine-tuned MuRIL classifier. Returns the probability that a prompt is an attack."""
import os

import config

_pipe = None  # loaded once, reused for every request


def load():
    """Load the model on first use (downloads from Hugging Face if needed)."""
    global _pipe
    if _pipe is None:
        from transformers import pipeline  # imported lazily so tests don't need the model
        _pipe = pipeline(
            "text-classification",
            model=config.CLASSIFIER_SOURCE,
            token=os.getenv("HF_TOKEN") or None,
            top_k=None,  # return the score of every label
        )
    return _pipe


def attack_probability(text: str) -> float:
    """Probability (0..1) that `text` is an attack."""
    out = load()(text, truncation=True, max_length=256)
    if out and isinstance(out[0], list):  # some versions nest the list
        out = out[0]
    for item in out:
        if str(item["label"]).upper() in ("ATTACK", "LABEL_1", "1", "INJECTION"):
            return float(item["score"])
    raise RuntimeError(f"No ATTACK label found in classifier output: {out}")
