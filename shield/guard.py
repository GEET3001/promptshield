"""Layer 6: output guard. Blocks replies that leak the canary, the admin code or the system prompt."""
import base64
import re

import config
from shield import chatbot

NGRAM = 8  # this many consecutive system-prompt words in a reply counts as a leak


def _words(text: str):
    return re.findall(r"\w+", text.lower())


def _alnum(text: str) -> str:
    """Lowercase and keep only letters/digits, so 'A-d m.i n' matches 'admin'."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _secret_forms(secret: str) -> set:
    """Plain, reversed, base64 and hex versions of a secret (all normalised)."""
    raw = secret.encode()
    plain = _alnum(secret)
    forms = {plain, plain[::-1], _alnum(base64.b64encode(raw).decode()), raw.hex()}
    return {f for f in forms if len(f) >= 4}  # ignore tiny strings to avoid false positives


def check(reply: str):
    """Return (leaked, reason)."""
    squashed = _alnum(reply)
    for label, secret in (("canary", config.get_canary()), ("admin_code", config.get_admin_code())):
        if secret and any(form in squashed for form in _secret_forms(secret)):
            return True, label
    sys_words = _words(chatbot.get_system_prompt())
    sys_ngrams = {tuple(sys_words[i:i + NGRAM]) for i in range(len(sys_words) - NGRAM + 1)}
    rep_words = _words(reply)
    for i in range(len(rep_words) - NGRAM + 1):
        if tuple(rep_words[i:i + NGRAM]) in sys_ngrams:
            return True, "system_prompt"
    return False, None


def is_leak(reply: str) -> bool:
    return check(reply)[0]
