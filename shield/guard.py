"""Layer 6: output guard. Blocks replies that leak the canary, the admin code or the system prompt."""
import re

import config
from shield import chatbot

NGRAM = 8  # this many consecutive system-prompt words in a reply counts as a leak


def _words(text: str):
    return re.findall(r"\w+", text.lower())


def check(reply: str):
    """Return (leaked, reason)."""
    low = reply.lower()
    for label, secret in (("canary", config.get_canary()), ("admin_code", config.get_admin_code())):
        if secret and secret.lower() in low:
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
