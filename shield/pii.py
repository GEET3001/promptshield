"""Layer 1: mask Indian PII with regexes before anything else sees the text."""
import re

# Order matters: email first, then the longer Aadhaar number, then PAN, then phone.
_PATTERNS = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("AADHAAR", re.compile(r"(?<!\d)[2-9]\d{3}\s?\d{4}\s?\d{4}(?!\d)")),
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    ("PHONE", re.compile(r"(?:\+91[\s-]?)?(?<!\d)[6-9]\d{9}(?!\d)")),
]


def mask(text: str):
    """Return (masked_text, entity_types). Raw values are never returned or stored."""
    entities = []
    for name, pattern in _PATTERNS:
        text, n = pattern.subn(f"<{name}>", text)
        entities.extend([name] * n)
    return text, entities
