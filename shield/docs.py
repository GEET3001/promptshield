"""Document helpers for the assistant: read a file, split it, scan it for hidden attacks, pick passages."""
import io
import re

import config
from shield import classifier, rules

CHUNK_CHARS = 600


def extract_text(name: str, data: bytes) -> str:
    """Return plain text from a .pdf, or from any text-like file (txt, md, csv)."""
    if name.lower().endswith(".pdf"):
        from pypdf import PdfReader  # lazy import
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    return data.decode("utf-8", errors="replace")


def make_chunks(text: str):
    """Split on blank lines, then merge short paragraphs and cut long ones to about CHUNK_CHARS."""
    chunks, buf = [], ""
    for para in re.split(r"\n\s*\n", text):
        para = re.sub(r"\s+", " ", para).strip()
        if not para:
            continue
        while len(para) > CHUNK_CHARS * 1.5:  # cut very long paragraphs at a sentence end if possible
            cut = para.rfind(". ", 0, CHUNK_CHARS) + 1 or CHUNK_CHARS
            chunks.append(para[:cut].strip())
            para = para[cut:].strip()
        if buf and len(buf) + len(para) > CHUNK_CHARS:
            chunks.append(buf)
            buf = ""
        buf = f"{buf} {para}".strip()
    if buf:
        chunks.append(buf)
    return chunks


def scan(chunks):
    """Find passages that look like instructions aimed at the AI. Returns [{index, reason, score}]."""
    flags = []
    flagged = set()
    # An attack sentence can be cut in two by chunking, so also check each seam between neighbours.
    for i in range(1, len(chunks)):
        seam = chunks[i - 1][-200:] + " " + chunks[i][:200]
        hit, attack_type, _ = rules.check(seam)
        if hit and not rules.check(chunks[i - 1])[0] and not rules.check(chunks[i])[0]:
            for j in (i - 1, i):
                flagged.add(j)
                flags.append({"index": j, "reason": f"attack pattern split across passages ({attack_type})", "score": None})
    for i, chunk in enumerate(chunks):
        if i in flagged:
            continue
        hit, attack_type, _ = rules.check(chunk)
        if hit:
            flags.append({"index": i, "reason": f"matches a known attack pattern ({attack_type})", "score": None})
            continue
        try:
            p = classifier.attack_probability(chunk)
        except Exception:
            continue  # classifier unavailable: rules alone still ran
        if p >= config.BLOCK_T:
            flags.append({"index": i, "reason": "classifier scored it as an attack", "score": round(p, 3)})
    return flags


def select(chunks, question, exclude=frozenset(), max_chars=6000, k=8):
    """Pick the passages that share the most words with the question (original order kept)."""
    words = {w for w in re.findall(r"\w+", question.lower()) if len(w) > 3}
    scored = [(sum(w in c.lower() for w in words), i) for i, c in enumerate(chunks) if i not in exclude]
    top = [i for s, i in sorted(scored, key=lambda t: (-t[0], t[1])) if s > 0][:k]
    if not top:  # e.g. a Hindi question: fall back to the start of the document
        top = [i for _, i in scored][:k]
    picked, total = [], 0
    for i in sorted(top):
        if total + len(chunks[i]) > max_chars:
            break
        picked.append(chunks[i])
        total += len(chunks[i])
    return "\n\n".join(picked)
