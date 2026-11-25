"""The request flow: PII -> rules -> classifier -> (judge) -> chatbot -> output guard -> log."""
import time

import config
from shield import chatbot, classifier, guard, judge, log, pii, rules

RETRY_MSG = "The safety check is temporarily unavailable. Please try again."
LLM_ERROR_MSG = "The assistant is temporarily unavailable. Please try again."


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def run(message: str, shield_on: bool = True) -> dict:
    """Process one user message. shield_on=False skips PII, rules, classifier, judge and output guard."""
    t_start = time.perf_counter()
    lat = {k: 0.0 for k in ("pii", "rules", "classifier", "judge", "llm", "output_guard", "total")}
    res = {"verdict": "allowed", "reply": "", "blocked_by": None, "risk_score": None,
           "attack_type": None, "masked_entities": [], "latency_ms": lat}
    text = (message or "").strip()[:config.MAX_CHARS]
    logged_prompt = pii.mask(text)[0]  # we only ever log the masked text

    def finish():
        lat["total"] = _ms(t_start)
        try:
            log.log_request(shield_on, logged_prompt, res)
        except Exception:  # logging must never break a request
            pass
        return res

    def block(by, reply=None, attack_type=None):
        res.update(verdict="blocked", reply=reply or config.REFUSAL, blocked_by=by)
        if attack_type:
            res["attack_type"] = attack_type
        return finish()

    llm_input = text
    if shield_on:
        # 1. PII masker
        if config.USE_PII:
            t = time.perf_counter()
            llm_input, res["masked_entities"] = pii.mask(text)
            lat["pii"] = _ms(t)
        # 2. Rule filter
        if config.USE_RULES:
            t = time.perf_counter()
            hit, attack_type, _ = rules.check(llm_input)
            lat["rules"] = _ms(t)
            if hit:
                return block("rules", attack_type=attack_type)
        # 3. Classifier. If it is off or fails to load, p stays None and the judge decides.
        p = None
        if config.USE_CLASSIFIER:
            t = time.perf_counter()
            try:
                p = classifier.attack_probability(llm_input)
                res["risk_score"] = round(p, 4)
            except Exception:
                p = None
            lat["classifier"] = _ms(t)
            if p is not None and p >= config.BLOCK_T:
                return block("classifier")
        # 4. LLM judge for the grey zone (fail closed on any error)
        if config.USE_JUDGE and (p is None or p >= config.JUDGE_T):
            t = time.perf_counter()
            verdict = judge.judge(llm_input)
            lat["judge"] = _ms(t)
            if verdict["error"]:
                return block("judge", reply=RETRY_MSG)
            if verdict["verdict"] == "ATTACK":
                return block("judge", attack_type=verdict["attack_type"])

    # 5. Chatbot LLM
    t = time.perf_counter()
    if config.SKIP_LLM:
        reply = "[LLM call skipped]"
    else:
        try:
            reply = chatbot.chat(llm_input)
        except Exception:
            reply = LLM_ERROR_MSG
    lat["llm"] = _ms(t)

    # 6. Output guard
    if shield_on and config.USE_OUTPUT_GUARD and not config.SKIP_LLM:
        t = time.perf_counter()
        leaked, _ = guard.check(reply)
        lat["output_guard"] = _ms(t)
        if leaked:
            return block("output_guard")

    res["reply"] = reply
    return finish()
