"""Layer 2: regex rule filter (English, Hinglish and Hindi). A match means BLOCK."""
import base64
import re

# Undo simple "leetspeak" obfuscation: 1gn0re -> ignore
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s"})
_ZERO_WIDTH = re.compile("[​‌‍⁠﻿]")
_B64_TOKEN = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")


def _decode_base64_tokens(text: str):
    """Find Base64-looking tokens (>= 16 chars) and return their readable decodings."""
    decoded = []
    for token in _B64_TOKEN.findall(text):
        try:
            raw = base64.b64decode(token + "=" * (-len(token) % 4), validate=True)
            readable = raw.decode("utf-8")
        except Exception:
            continue  # not valid Base64 / not text
        if len(readable) >= 6 and readable.isprintable():
            decoded.append(readable)
    return decoded


def normalise(text: str) -> str:
    """Lowercase, collapse spaces, undo leetspeak, and append any decoded Base64."""
    text = text + " " + " ".join(_decode_base64_tokens(text))  # decode before lowercasing
    text = _ZERO_WIDTH.sub("", text).lower().translate(_LEET)
    return re.sub(r"\s+", " ", text).strip()


# (attack_type, pattern_name, regex). Applied to the NORMALISED text.
_RAW_RULES = [
    # ---- direct_override ----
    ("direct_override", "ignore_previous",
     r"\b(ignore|disregard|forget|override|bypass|skip)\b.{0,30}\b(previous|prior|above|earlier|all|any|your|the)\b.{0,20}\b(instructions?|rules?|prompts?|guidelines?|directions?|commands?)\b"),
    ("direct_override", "new_instructions", r"\b(new|updated|real) instructions?\s*:"),
    ("direct_override", "from_now_on", r"\bfrom now on\b.{0,40}\b(you (will|must|are|shall)|ignore|only answer)\b"),
    ("direct_override", "stop_following", r"\bstop (following|obeying)\b.{0,30}\b(rules|instructions|guidelines)\b"),
    ("direct_override", "do_anything_now", r"\bdo anything now\b|\bdan mode\b|\byou are dan\b"),
    ("direct_override", "act_without_limits",
     r"\b(act|respond|answer|behave|reply)\b.{0,20}\b(without|with no) (any )?(restrictions|filters|limitations|censorship)\b"),
    ("direct_override", "enable_special_mode",
     r"\b(enable|enter|activate|switch to|turn on)\b.{0,15}\b(developer|debug|god|admin|sudo|unrestricted) mode\b"),
    ("direct_override", "disable_safety",
     r"\b(disable|turn off|deactivate|remove)\b.{0,20}\b(safety|guardrails?|content filters?|content policy|moderation)\b"),
    ("direct_override", "override_system", r"\boverride (the )?(system|safety|your (rules|instructions))\b"),
    ("direct_override", "end_of_prompt_marker", r"(</?system>|\[/?inst\]|### ?system|<\|im_start\|>)"),
    # ---- prompt_leak ----
    ("prompt_leak", "reveal_prompt",
     r"\b(reveal|show|print|display|repeat|output|tell|give|leak|share|write|recite|dump|expose)\b.{0,30}\b(your|the|ur)\s+(system|initial|original|hidden|secret|internal|first)\s+(prompt|instructions?|message|rules)\b"),
    ("prompt_leak", "what_are_your_hidden_instructions",
     r"\bwhat (are|were|is) your (system|initial|original|hidden|secret|internal) (instructions?|prompt|rules|message)\b"),
    ("prompt_leak", "repeat_above", r"\brepeat (the |all )?(words|text|everything|content) (above|before)\b"),
    ("prompt_leak", "verbatim_prompt", r"\bverbatim\b.{0,30}\b(prompt|instructions)\b|\bbeginning of (this|the) conversation\b"),
    ("prompt_leak", "ask_secret_code",
     r"\b(reveal|tell|show|give|what is|what's|share|print|say)\b.{0,25}\b(admin(istrator)?|secret|master|internal) (code|password|key|token)\b"),
    ("prompt_leak", "ask_canary", r"\bcanary\b.{0,15}\b(token|word|string|value)\b"),
    # ---- roleplay_jailbreak ----
    ("roleplay_jailbreak", "pretend_no_rules",
     r"\b(pretend|imagine|act|roleplay|role-play|behave)\b.{0,30}\b(you are|you're|to be|as|that you)\b.{0,40}\b(no (rules|restrictions|limits)|unrestricted|unfiltered|evil|uncensored|without (rules|restrictions|limits))\b"),
    ("roleplay_jailbreak", "persona_unrestricted",
     r"\byou are (now )?(dan|stan|aim|an? (unrestricted|unfiltered|uncensored|evil) (ai|assistant|bot|model))\b"),
    ("roleplay_jailbreak", "fiction_bypass",
     r"\b(hypothetical(ly)?|fictional|in a story|for a (movie|novel|game))\b.{0,60}\b(ignore (the )?rules|no rules|how to (make|build) (a )?(bomb|weapon|malware)|bypass)\b"),
    ("roleplay_jailbreak", "grandma_trick",
     r"\bmy (late |dead |deceased )?(grandmother|grandma)\b.{0,60}\b(used to|would) (read|tell|say)\b.{0,60}\b(key|password|prompt|instructions|code)\b"),
    ("roleplay_jailbreak", "opposite_mode", r"\b(opposite|evil|jailbreak|chaos) mode\b"),
    # ---- obfuscation ----
    ("obfuscation", "decode_then_obey",
     r"\b(decode|base64|rot13|hex|binary)\b.{0,30}\b(and|then)\b.{0,20}\b(execute|follow|run|obey)\b"),
    ("obfuscation", "spaced_letters", r"(?:\b[a-z] ){7,}[a-z]\b"),
    ("obfuscation", "reversed_ignore", r"\berongi\b|\bsdrawkcab\b"),
    # ---- payload_split ----
    ("payload_split", "remember_then_combine",
     r"\b(first|part|step) (1|one|a)\b.{0,60}\b(remember|store|save|memorize)\b.{0,60}\b(later|next|then|combine|concatenate)\b"),
    ("payload_split", "concatenate_and_run",
     r"\b(concatenate|combine|join)\b.{0,40}\b(strings?|parts?|variables?)\b.{0,40}\b(and|then)\b.{0,20}\b(execute|follow|run|obey)\b"),
    ("payload_split", "variable_assignment",
     r"\b(a|x|var1)\s*=\s*[\"'][^\"']+[\"'].{0,60}\b(b|y|var2)\s*=\s*[\"']"),
    # ---- language_switch: Hinglish (Roman script) ----
    ("language_switch", "hinglish_bhool_jao", r"\b(bhool|bhul)\s*(jao|jaao|ja|jana)\b"),
    ("language_switch", "hinglish_pichhle_nirdesh",
     r"\b(pichhle|pichle|pehle (ke|wale)|purane|saare|sare|sabhi)\b.{0,20}\b(nirdesh|nirdeshon|instructions?|rules?|niyam|niyamon)\b"),
    ("language_switch", "hinglish_ignore_karo",
     r"\b(ignore|andekha|anadekha|nazarandaz)\s*(kar|karo|kardo|kar do|kijiye)\b.{0,30}\b(nirdesh|rules?|instructions?|niyam|sab)\b"),
    ("language_switch", "hinglish_rules_hata",
     r"\b(sab|saare|sare) (rules?|niyam|instructions?|nirdesh)\b.{0,20}\b(bhool|ignore|hata|tod|chhod|chod)"),
    ("language_switch", "hinglish_reveal_secret",
     r"\b(system prompt|admin code|secret code)\b.{0,30}\b(batao|bata do|dikhao|dikha do|bolo|de do|likho)\b"),
    ("language_switch", "hinglish_no_rules",
     r"\b(bina|without) (kisi )?(rules?|restriction|pabandi|niyam|rok-?tok)\b.{0,20}\b(jawab|reply|answer|baat|kaam)\b"),
    # ---- language_switch: Hindi (Devanagari). No \b: it is unreliable around Devanagari marks ----
    ("language_switch", "hindi_ignore_instructions", r"(निर्देश|नियम|आदेश)\S*.{0,20}(अनदेखा|नज़रअंदाज़|नजरअंदाज|भूल जाओ|भूल जाइए)"),
    ("language_switch", "hindi_ignore_instructions_rev", r"(अनदेखा|नज़रअंदाज़|नजरअंदाज|भूल जाओ|भूल जाइए).{0,30}(निर्देश|नियम|आदेश)"),
    ("language_switch", "hindi_reveal_secret",
     r"(सिस्टम प्रॉम्प्ट|सिस्टम प्रोम्प्ट|एडमिन कोड|गुप्त कोड|सीक्रेट कोड).{0,30}(बताओ|बताइए|दिखाओ|दिखाइए|बता दो|लिखो)"),
]

RULES = [(atype, name, re.compile(rx, re.DOTALL)) for atype, name, rx in _RAW_RULES]


def check(text: str):
    """Return (matched, attack_type, pattern_name). First matching rule wins."""
    norm = normalise(text)
    for attack_type, name, pattern in RULES:
        if pattern.search(norm):
            return True, attack_type, name
    return False, None, None
