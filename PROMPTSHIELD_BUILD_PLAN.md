# PromptShield — Lean Build Plan for Claude Code (Pro, budget mode)

**Budget target:** finish the coding in **≤ 60% of one Claude Pro 5-hour window**.
**How:** 10 large prompts + up to 3 fix-up prompts (13 max). Claude writes code; the team runs heavy jobs (installs, Colab training, deployment clicks) and does all reading and report writing outside Claude Code.

---

## 0. Before you open Claude Code (team does this, costs no Claude usage)

1. **Fill in the DECISIONS block (section 2) completely.** Claude must not ask questions that are already answered there; every question costs a round-trip.
2. Create accounts and keys: GitHub, Hugging Face (+ a *write* access token), Google (Colab), Gemini API key (aistudio.google.com/app/apikey), Groq API key (console.groq.com/keys).
3. Install Python 3.11, VS Code (+ Python extension), GitHub Desktop. Create the GitHub repo `promptshield` (Python `.gitignore`, MIT licence), clone it, and put this file and `CLAUDE.md` in the root.
4. Do your own reading (OWASP LLM01 and the papers in section 7), play Gandalf (gandalf.lakera.ai), and write 30 attacks + 15 "hard negative" safe prompts into `data/handwritten.csv` with columns `text,label,attack_type,language,source` (see section 3).
5. **Use these Claude Code habits (they matter more than anything else for the budget):**
   - Switch to the Sonnet model before starting (`/model` → Sonnet). Don't use Opus for this project.
   - Run **`/clear` after every prompt**. A fresh context per prompt costs far less than one long conversation. `PROGRESS.md` carries the memory between prompts.
   - Check **`/usage`** after every prompt and write the % in `PROGRESS.md`. **If usage passes 60%, stop** and continue in the next window from the next prompt.
   - Run long commands (pip install, training, Streamlit, uvicorn) **yourself** in the VS Code terminal. Paste **only the last ~20 lines of an error** to Claude, never full logs.
   - Copy each prompt from section 5 exactly. Don't chat with Claude between prompts; save questions for the fix-up prompts.

---

## 1. Project context (Claude: read once, don't re-explain it back)

**PromptShield: Defending LLM Apps Against Prompt Injection.** A gateway between users and an LLM that blocks prompt-injection, jailbreak and leak attacks with a layered pipeline, plus a Streamlit attack playground and dashboard. Research angle: English-focused detectors miss **Hindi and Hinglish** attacks; the team's fine-tuned **MuRIL** classifier should catch them.

**Request flow (`run(message, shield_on)`):**
1. PII masker (regex: Aadhaar, PAN, Indian phone, email) →
2. Rule filter (regex; match → BLOCK) →
3. Classifier (attack probability p; p ≥ BLOCK_T → BLOCK; JUDGE_T ≤ p < BLOCK_T → step 4; p < JUDGE_T → step 5) →
4. LLM judge (JSON verdict; ATTACK → BLOCK; API error → BLOCK "please try again", i.e. fail closed) →
5. Chatbot LLM (system prompt holds `ADMIN_CODE` and `CANARY`) →
6. Output guard (reply contains canary, admin code, or ≥ 8 consecutive words of the system prompt → BLOCK) →
7. Log to SQLite (masked prompt only).
`shield_on=False` skips 1–4 and 6 (still logs).

**Team:** final-year CSE students, comfortable with Python/ML, **new to the command line**. Explain any command in one sentence. They must understand every line for the viva, so keep code plain and commented.

**Fixed scope (do not add features):** regex PII (no Presidio/spaCy), one fine-tuned model (MuRIL) + baselines, single-process app (no microservices), manual Space upload (no CI), 3 evaluation experiments. Out of scope: indirect injection, garak, HackAPrompt, literature summaries, report drafting.

---

## 2. DECISIONS (team fills this BEFORE starting; Claude reads, never re-asks)

```text
OS of team laptops:              __windows__________  (Windows / macOS / Linux)
Hugging Face username:           ___GEET3001_________
Chatbot LLM provider + model:    Gemini / ____________   (check current free model name in Gemini docs)
Judge LLM provider + model:      Groq   / ____________   (check current free model name in Groq docs)
Block refusal message:           "Sorry, I can't help with that request."
False-positive target for block: 2%
Judge band starting value:       JUDGE_T = 0.4
Translate Hindi/Hinglish via:    Gemini API script (team reviews 50 rows)
Target dataset size:             ~4,000 rows, 40–50% attacks, ≥ 15% Hindi/Hinglish
Demo bot persona:                "Riverside Institute of Technology Help Desk" (fictional)
Charts in dashboard:             Streamlit native (st.bar_chart)
Space name / visibility:         promptshield / public
```

Claude: ask a question **only** if something here is blank or a fixed choice turns out to be impossible (e.g. a dataset or model is gone). Ask everything you need in **one** message with numbered options and a recommendation.

---

## 3. Shared specs

**Dataset columns:** `text` (≤ 2000 chars) · `label` (0 safe, 1 attack) · `attack_type` · `language` (`en`/`hi`/`hinglish`) · `source`.

**attack_type values:** `direct_override`, `prompt_leak`, `roleplay_jailbreak`, `obfuscation`, `payload_split`, `language_switch`, `none`.

**`run()` return dict:**
`{"verdict": "allowed"|"blocked", "reply": str, "blocked_by": None|"rules"|"classifier"|"judge"|"output_guard", "risk_score": float|None, "attack_type": str|None, "masked_entities": list, "latency_ms": {"pii","rules","classifier","judge","llm","output_guard","total"}}`

**Env vars (`.env`, never committed):** `GEMINI_API_KEY`, `GROQ_API_KEY`, `HF_TOKEN`, `ADMIN_CODE`, `CANARY`.

**Repo layout (final):**
```
config.py  requirements.txt  .env.example  PROGRESS.md  README.md
data/            handwritten.csv, README.md (dataset card)
scripts/         build_dataset.py, baselines.py, finetune.py, metrics.py, run_scripted.py, evaluate.py
shield/          pii.py, rules.py, classifier.py, judge.py, chatbot.py, guard.py, log.py, pipeline.py
api.py           (FastAPI: POST /chat → run())
app/             Home.py, pages/1_Playground.py, pages/2_Dashboard.py
demo/            scripted_attacks.csv
tests/           test_shield.py
results/         csv tables + png figures
Dockerfile       (for the HF Space)
```

---

## 4. Rules for Claude (follow strictly — they protect the budget)

1. Do exactly the current prompt. Don't start the next one, and don't add features outside section 1's scope.
2. **Write all files for a prompt in one pass.** Don't explore the repo with many reads; read only `PROGRESS.md`, `config.py` and files the prompt names.
3. Don't run installs, training, servers or long tests yourself unless the prompt says so. Tell the user the exact command instead.
4. Don't web-search or fetch pages. If you're unsure about a current API/model name, write it as a clearly marked `config.py` value and tell the user to check it.
5. Keep your final message **≤ 10 lines**: files created, the command(s) the user runs next, what "success" looks like. No code recap.
6. Append one line to `PROGRESS.md` per prompt: `P<n> done — <what> — usage: __% (user fills)`.
7. Never hard-code or print secrets; never use `test.csv` for training or tuning; never invent results.
8. Ask questions only per section 2's rule.

---

## 5. The prompts (copy one at a time; `/clear` between them)

### P1 — Project skeleton (≈ 1 prompt)
```text
Read PROMPTSHIELD_BUILD_PLAN.md sections 1–4. Do prompt P1 only.
Create: the folder layout from section 3 (empty __init__.py in shield/), .gitignore additions
(.env, .venv/, __pycache__/, *.db, results/*.tmp), .env.example, requirements.txt
(python-dotenv, google-genai, groq, pandas, numpy, scikit-learn, matplotlib, transformers,
torch, datasets, huggingface_hub, fastapi, uvicorn, streamlit, requests, pytest),
config.py (all model names, thresholds BLOCK_T/JUDGE_T, layer on/off flags, DB path,
MAX_CHARS, refusal message, getters for ADMIN_CODE/CANARY from env — values from the
DECISIONS block), smoke_test.py (calls chatbot provider and judge provider once each and
prints replies), and PROGRESS.md with a stage table.
Then tell me the 3 commands to run: create venv, pip install, python smoke_test.py.
```
**Team after P1:** create `.venv` (VS Code: Ctrl+Shift+P → "Python: Create Environment"), `pip install -r requirements.txt`, copy `.env.example` → `.env` and fill keys, run `python smoke_test.py`. Commit with GitHub Desktop.

### P2 — Dataset builder (≈ 1 prompt)
```text
Do prompt P2 from PROMPTSHIELD_BUILD_PLAN.md. Write scripts/build_dataset.py, runnable in
Colab or locally, that: loads deepset/prompt-injections, Lakera/gandalf_ignore_instructions
(all label 1), jackhhao/jailbreak-classification (columns prompt,type: jailbreak→1,
benign→0) and data/handwritten.csv; maps all to the section-3 schema; adds ~200 generated
hard-negative safe prompts from a hard-coded list of templates; selects 300 attacks + 300
safe English rows and translates them to Hindi (Devanagari) and Hinglish via the Gemini
API in batches of 20 with JSON output and retry; writes data/translation_check.csv (50
random translated rows) for human review; cleans (strip, drop empty, truncate MAX_CHARS,
dedupe on lowercased whitespace-collapsed text); caps any single source at 40%; splits
70/15/15 stratified on label+language with random_state=42; asserts no text overlaps
across splits; saves train/val/test CSVs to data/; prints a counts table
(label × language × split); optional --push flag pushes a private HF dataset
<username>/promptshield-data. Print each source's real columns first and fail with a
clear message if they differ from what you expect. Also write data/README.md as a short
dataset card template with the counts table to be pasted in.
```
**Team after P2:** run it (Colab is fine), review `translation_check.csv`, fix or delete bad rows, re-run with `--push`. Paste the counts table into `data/README.md`.

### P3 — Rules + baselines + metrics (≈ 1 prompt)
```text
Do prompt P3. Write:
1) shield/rules.py: normalise() (lowercase, collapse spaces, undo leetspeak 0→o 1→i 3→e
4→a 5→s @→a $→s, decode Base64-looking tokens ≥16 chars and append) and check(text) →
(matched, attack_type, pattern_name) using 30–40 compiled regexes grouped by attack_type,
including Hinglish patterns (e.g. bhool jao, nirdesh, sab rules).
2) scripts/metrics.py: score(y_true, y_pred, languages) → dict with accuracy, precision,
recall, f1, fpr overall plus f1_en and f1_hi_hinglish.
3) scripts/baselines.py: on data/val.csv, scores (a) the rule filter, (b) TF-IDF
char_wb (2,5) + LogisticRegression trained on train.csv, (c) protectai/
deberta-v3-base-prompt-injection-v2 zero-shot (map its injection label→1, safe→0; read
label names from model.config.id2label). Saves results/baselines_val.csv and prints it.
Tell me the command to run it.
```

### P4 — Fine-tune MuRIL (≈ 1 prompt; training runs in Colab, not Claude)
```text
Do prompt P4. Write scripts/finetune.py for a Colab T4 GPU: loads train/val CSVs (or the
HF dataset), fine-tunes google/muril-base-cased with Trainer (lr 2e-5, batch 16, 4
epochs, weight_decay 0.01, warmup_ratio 0.1, eval/save per epoch, best model by f1,
fp16, seed 42, max_length 256, id2label {0:SAFE,1:ATTACK}, output_dir argument so it can
point to Google Drive); after training: scores val with scripts/metrics.py and appends to
results/baselines_val.csv as "muril"; computes BLOCK_T = lowest threshold with val FPR ≤
target and reports how many val rows fall in [JUDGE_T, BLOCK_T); saves
results/pr_curve.png; exports results/val_errors.csv (text, label, pred, prob,
attack_type, language); measures mean CPU latency over 200 val prompts; with --push
uploads the model to a private HF repo <username>/promptshield-muril. Add a 6-line
comment block at the top with the exact Colab cells to run. Tell me what values to copy
into config.py afterwards.
```
**Team after P4 (gate 1):** run in Colab, copy `BLOCK_T` into `config.py`, read 50 rows of `val_errors.csv` and note the failure patterns for the report. MuRIL must beat all baselines on F1 overall and on Hindi/Hinglish. If it doesn't, use **fix-up prompt F1** (section 5b).

### P5 — The shield pipeline (≈ 1 prompt, the biggest)
```text
Do prompt P5. Implement the section-1 request flow exactly:
shield/pii.py (regex mask: Aadhaar \b[2-9]\d{3}\s?\d{4}\s?\d{4}\b → <AADHAAR>, PAN
\b[A-Z]{5}[0-9]{4}[A-Z]\b → <PAN>, Indian mobile (?:\+91[\s-]?)?\b[6-9]\d{9}\b → <PHONE>,
email → <EMAIL>; returns masked text + entity list), shield/classifier.py (loads the HF
model once via pipeline with HF_TOKEN, returns attack probability), shield/judge.py
(provider from config, temperature 0, JSON-only prompt with verdict + attack_type +
reason, robust parse, timeout, fail closed), shield/chatbot.py (Riverside Help Desk
system prompt containing ADMIN_CODE and CANARY from env; provider from config),
shield/guard.py (canary / admin code / ≥8 consecutive system-prompt words → block),
shield/log.py (SQLite table: id, ts, shield_on, prompt_masked, verdict, blocked_by,
attack_type, risk_score, latency_total_ms, latency_json), shield/pipeline.py run()
returning the section-3 dict, timing each layer with perf_counter and honouring config
layer flags, and api.py (FastAPI POST /chat + GET /health with Pydantic models).
Keep each file short and commented. Tell me the command to start the API and one curl-free
way to test it (the /docs page).
```

### P6 — Tests + demo attacks (≈ 1 prompt)
```text
Do prompt P6. Write tests/test_shield.py (pytest): rules catch 5 attacks and pass 5 hard
negatives; pii masks each ID type; guard blocks canary/admin-code leaks; pipeline returns
blocked_by="rules" for an obvious attack and verdict "allowed" for a safe prompt with the
judge and LLM mocked (monkeypatch) so tests need no API calls or model download.
Write demo/scripted_attacks.csv with 20 attacks across all attack_types (≥4 Hindi/
Hinglish) + 3 hard negatives, columns text,attack_type,language, and
scripts/run_scripted.py that runs each through run() with shield off and on and saves
results/scripted_results.csv (leaked_off, blocked_on, blocked_by). Tell me the two
commands to run.
```
**Team after P6:** run `pytest` and `python scripts/run_scripted.py`. You need ≥ 5 leaks with shield off. If fewer, weaken the system prompt in `shield/chatbot.py` yourselves (remove "never reveal") and note this in the report.

### P7 — Streamlit app (≈ 1 prompt)
```text
Do prompt P7. Write app/Home.py (set_page_config wide, title, 1-paragraph explanation,
flow list, links), app/pages/1_Playground.py (st.toggle shield, st.chat_input/
st.chat_message with history in session_state, calls run() directly, shows green
Allowed or red "Blocked by <layer>" + risk score + attack type, expander with per-layer
latency, sidebar buttons for 5 attacks from demo/scripted_attacks.csv + 1 hard negative,
classifier loaded via st.cache_resource), app/pages/2_Dashboard.py (pd.read_sql from the
log, shield filter, refresh button, st.metric for total / % blocked / avg latency,
st.bar_chart for blocks by layer and by attack type, table of 20 latest blocked prompts,
empty-state message). Tell me the run command.
```

### P8 — Deployment files (≈ 1 prompt; deployment clicks are the team's)
```text
Do prompt P8. Hugging Face Spaces no longer has a Streamlit SDK; Streamlit runs via the
Docker SDK. Write a Dockerfile (python:3.11-slim, non-root user with uid 1000 as HF
requires, install requirements, copy repo, expose 8501, run streamlit run app/Home.py
--server.port=8501 --server.address=0.0.0.0) and a SPACE_README.md containing the YAML
header the Space needs (sdk: docker, app_port: 8501, title, emoji) to be pasted into the
Space's README.md. Make sure the SQLite path is writable inside the container. List the
exact clicks to create the Space, upload files, and add the 5 secrets. ≤ 15 lines.
```
**Team after P8 (gate 2):** create the Space (Docker → blank or Streamlit template), upload files via the website, add secrets, watch the Logs tab. If the build fails, use **fix-up prompt F2** with the last 20 log lines. Test the link from a phone; run the 20 scripted attacks on it.

### P9 — Evaluation (≈ 1 prompt)
```text
Do prompt P9. Write scripts/evaluate.py that, using data/test.csv once:
(1) model comparison: rules, TF-IDF, ProtectAI, MuRIL → results/exp1_models.csv;
(2) language gap: f1_en vs f1_hi_hinglish per model → results/exp2_language.csv + bar
chart png; (3) layer ablation: run() over 200 test prompts with the full pipeline and
with each of rules/classifier/judge disabled via config flags → % attacks caught,
% safe wrongly blocked, mean and p95 latency → results/exp3_ablation.csv + latency bar
png (judge calls are real; add --no-judge to skip it if API limits are tight);
plus a confusion matrix png for MuRIL. Fixed seeds. Print a 1-line summary per experiment.
```
**Team after P9:** run it; write the results chapter yourselves from the CSVs and PNGs.

### P10 — README + viva sheet (≈ 1 prompt)
```text
Do prompt P10. Write README.md (problem, flow diagram in text, features, how to run
locally, results tables pulled from results/*.csv, demo link placeholder, dataset/model
links, team placeholder, licence) and docs/viva.md: 10 likely viva questions with short
answers grounded in this repo (why not just a system-prompt instruction, why MuRIL /
transliteration, how thresholds were chosen, fail-closed judge, test-set leakage
prevention, what attacks still get through, scaling bottleneck, direct vs indirect
injection, why regex PII, why char n-grams for TF-IDF). Then grep the repo for anything
that looks like an API key or the admin code/canary and report findings.
```

### 5b. Fix-up prompts (use only if needed; max 3 in total)
- **F1 — model didn't beat baselines:** `Read PROGRESS.md and results/val_errors.csv (first 60 rows only). Suggest the 3 most likely fixes ranked by effort, and implement the one I choose: ___.`
- **F2 — error:** `Error while running <command>. Last lines: <paste ≤ 20 lines>. Fix it with the smallest change; tell me what changed in ≤ 5 lines.`
- **F3 — free slot:** use for anything else, in one message with everything you need.

---

## 6. Budget sheet (fill in as you go)

| Prompt | Done | /usage % after |
| --- | --- | --- |
| P1 Skeleton | ☐ | |
| P2 Dataset | ☐ | |
| P3 Baselines | ☐ | |
| P4 Fine-tune | ☐ | |
| P5 Pipeline | ☐ | |
| P6 Tests + demo | ☐ | |
| P7 Streamlit | ☐ | |
| P8 Deploy files | ☐ | |
| P9 Evaluation | ☐ | |
| P10 README + viva | ☐ | |
| F1–F3 (if used) | ☐ | |

**If usage crosses 60% before P10:** stop, commit, and continue in the next window. P8–P10 are independent of each other, so they can go in any order.

**Do outside Claude Code (no Claude usage):** reading and literature review, Gandalf, writing handwritten attacks, reviewing translations, Colab training runs, Space setup, the classmate red-team session, report, slides, demo recording.

## 7. References (for the team's reading and the report)

OWASP LLM01 https://genai.owasp.org/llmrisk/llm01-prompt-injection/ · Perez & Ribeiro https://arxiv.org/abs/2211.09527 · Greshake et al. https://arxiv.org/abs/2302.12173 · HackAPrompt https://arxiv.org/abs/2311.16119 · NeMo Guardrails https://arxiv.org/abs/2310.10501 · MuRIL https://arxiv.org/abs/2103.10730 · LLM Guard https://github.com/protectai/llm-guard · deepset/prompt-injections https://huggingface.co/datasets/deepset/prompt-injections · Lakera/gandalf_ignore_instructions https://huggingface.co/datasets/Lakera/gandalf_ignore_instructions · jackhhao/jailbreak-classification https://huggingface.co/datasets/jackhhao/jailbreak-classification · ProtectAI model https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2 · MuRIL model https://huggingface.co/google/muril-base-cased · HF fine-tuning course https://huggingface.co/learn/llm-course/chapter3/1 · Streamlit https://docs.streamlit.io/ · Streamlit on Spaces https://huggingface.co/docs/hub/spaces-sdks-streamlit · FastAPI https://fastapi.tiangolo.com/tutorial/ · Gemini API https://ai.google.dev/gemini-api/docs/quickstart · Groq https://console.groq.com/docs/quickstart
