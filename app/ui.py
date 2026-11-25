"""Shared look for the PromptShield app: stylesheet, status chips and the shield trail."""
import html

import streamlit as st

INK, TEAL, RED, AMBER, LINE = "#14213D", "#0B7A75", "#B3261E", "#A15C00", "#C9D2E1"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap');
html, body, .stApp, [data-testid="stSidebar"], button, input, textarea {{ font-family: 'Instrument Sans', system-ui, sans-serif; }}
h1, h2, h3, .ps-title {{ font-family: 'Bricolage Grotesque', 'Instrument Sans', sans-serif; letter-spacing: -0.02em; color: {INK}; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2rem; max-width: 1280px; }}
[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid {LINE}; }}
[data-testid="stChatMessage"] {{ background: transparent; padding: 0.35rem 0; }}

.ps-brand {{ display: flex; align-items: center; gap: .6rem; margin-bottom: .2rem; }}
.ps-mark {{ width: 34px; height: 34px; border-radius: 9px; background: {INK}; color: #fff; display: grid; place-items: center; font-size: 1.1rem; }}
.ps-title {{ font-size: 1.35rem; font-weight: 700; margin: 0; }}
.ps-sub {{ color: #5B6785; font-size: .9rem; margin: 0 0 .6rem 0; }}
.ps-head h1 {{ font-size: 2.2rem; margin: 0 0 .2rem 0; }}
.ps-head p {{ color: #5B6785; margin: 0 0 1.1rem 0; max-width: 62ch; }}

.ps-doc {{ display: flex; flex-wrap: wrap; align-items: center; gap: .5rem 1rem; padding: .7rem 1rem; margin-bottom: 1rem;
          background: #fff; border-left: 4px solid {TEAL}; border-radius: 0 10px 10px 0; }}
.ps-doc b {{ color: {INK}; }}
.ps-doc span.meta {{ color: #5B6785; font-size: .88rem; }}

.ps-chip {{ display: inline-block; padding: .12rem .6rem; border-radius: 999px; font-size: .8rem; font-weight: 600; }}
.ps-chip.ok {{ background: #D6EFEC; color: {TEAL}; }}
.ps-chip.bad {{ background: #F7DAD7; color: {RED}; }}
.ps-chip.warn {{ background: #F6E4C8; color: {AMBER}; }}
.ps-chip.mute {{ background: #E3E8F0; color: #44506B; }}
.ps-note {{ color: #5B6785; font-size: .82rem; margin-top: .25rem; }}

.ps-trail-h {{ font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 1.15rem; color: {INK}; margin: 0 0 .15rem 0; }}
.ps-trail-s {{ color: #5B6785; font-size: .85rem; margin: 0 0 1rem 0; }}
.trail {{ border-left: 2px solid {LINE}; margin-left: 8px; padding-left: 20px; }}
.trail .step {{ position: relative; padding-bottom: 15px; }}
.trail .step .dot {{ position: absolute; left: -29px; top: 3px; width: 14px; height: 14px; border-radius: 50%; background: {LINE}; border: 2px solid #EEF1F6; }}
.trail .step.passed .dot {{ background: {TEAL}; }}
.trail .step.blocked .dot {{ background: {RED}; }}
.trail .step.warn .dot {{ background: {AMBER}; }}
.trail .step.off .dot {{ background: repeating-linear-gradient(45deg, {LINE}, {LINE} 3px, #EEF1F6 3px, #EEF1F6 6px); }}
.trail .step b {{ display: block; font-weight: 600; font-size: .95rem; color: {INK}; }}
.trail .step small {{ color: #5B6785; font-size: .82rem; }}
.trail .step.blocked b {{ color: {RED}; }}
.trail .step.skipped b, .trail .step.off b {{ color: #7A869F; font-weight: 500; }}
.ps-empty {{ color: #5B6785; padding: 2.5rem 0; max-width: 52ch; }}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def chip(text, kind="mute"):
    return f'<span class="ps-chip {kind}">{html.escape(text)}</span>'


STEP_TITLES = {"pii": "Hide personal data", "rules": "Check known attack patterns", "classifier": "Score the message",
               "judge": "Second opinion", "llm": "Answer from the document", "output_guard": "Check the reply for leaks"}
ORDER = ["pii", "rules", "classifier", "judge", "llm", "output_guard"]


def build_trail(res, shield_on, doc):
    """Turn one pipeline result into a list of (state, title, detail) for the trail."""
    lat, by, blocked = res["latency_ms"], res["blocked_by"], res["verdict"] == "blocked"
    steps = []
    if doc is not None:
        n = len(doc["flags"])
        if n == 0:
            steps.append(("passed", "Check the document", "No hidden instructions found"))
        elif shield_on:
            steps.append(("warn", "Check the document", f"{n} suspicious passage{'s' if n > 1 else ''} removed before answering"))
        else:
            steps.append(("warn", "Check the document", f"{n} suspicious passage{'s' if n > 1 else ''} sent to the assistant"))
    for key in ORDER:
        title = STEP_TITLES[key]
        if not shield_on and key != "llm":
            steps.append(("off", title, "Shield is off"))
        elif blocked and key == by:
            detail = {"rules": f"Matched {res['attack_type'] or 'a known pattern'}",
                      "classifier": f"Risk score {res['risk_score']}, above the block line",
                      "judge": (f"Judge flagged it as {res['attack_type']}" if res["attack_type"] else "Judge could not answer, so it was blocked"),
                      "output_guard": "The reply would have leaked a secret"}.get(key, "Blocked")
            steps.append(("blocked", title, detail))
        elif blocked and by in ORDER and ORDER.index(key) > ORDER.index(by):
            steps.append(("skipped", title, "Not reached"))
        else:
            ms = f"{lat.get(key, 0):.0f} ms"
            detail = {"pii": ("Hid " + ", ".join(sorted(set(res["masked_entities"])))) if res["masked_entities"] else "Nothing to hide",
                      "rules": "No known pattern matched",
                      "classifier": f"Risk score {res['risk_score']}" if res["risk_score"] is not None else "Not available, the judge covered it",
                      "judge": "Judge said it is safe" if lat.get("judge") else "Not needed, the score was low",
                      "llm": f"Answered in {lat.get('llm', 0) / 1000:.1f} s",
                      "output_guard": "Reply is clean"}[key]
            steps.append(("passed", title, detail if key == "llm" else f"{detail} ({ms})"))
    return steps


def trail_html(steps):
    rows = "".join(f'<div class="step {s}"><span class="dot"></span><b>{html.escape(t)}</b><small>{html.escape(d)}</small></div>'
                   for s, t, d in steps)
    return f'<div class="trail">{rows}</div>'
