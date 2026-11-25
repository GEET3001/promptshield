# 🛡️ PromptShield: Defending LLM Apps Against Prompt Injection

A gateway between users and an LLM chatbot that blocks prompt-injection, jailbreak and secret-leak attacks with a layered pipeline, plus a Streamlit attack playground and dashboard.
**Research angle:** English-focused detectors miss **Hindi and Hinglish** attacks; our fine-tuned **MuRIL** classifier is built to catch them.

## Request flow
```
user message
   │
   ▼
[1 PII masker]  Aadhaar / PAN / phone / email → <TOKENS>
   ▼
[2 Rule filter] ~40 regexes (EN / Hinglish / Hindi) ── match ──► BLOCK
   ▼
[3 Classifier]  MuRIL attack probability p
   │  p ≥ BLOCK_T ───────────────────────────────────────────► BLOCK
   │  JUDGE_T ≤ p < BLOCK_T ──► [4 LLM judge] ATTACK/error ──► BLOCK (fails closed)
   ▼  p < JUDGE_T (or judge says SAFE)
[5 Chatbot LLM]  system prompt holds ADMIN_CODE + CANARY
   ▼
[6 Output guard] canary / admin code / ≥8 system-prompt words in reply ──► BLOCK
   ▼
[7 SQLite log]   masked prompt only
```
`run(message, shield_on)` in `shield/pipeline.py` implements this; `shield_on=False` skips steps 1–4 and 6.

## Run locally (Windows)
```powershell
python -m venv .venv                 # create a private Python environment
.venv\Scripts\activate               # switch into it
pip install -r requirements.txt      # install libraries
copy .env.example .env               # then open .env and fill in the keys
python smoke_test.py                 # checks Gemini + Groq work
pytest -q                            # offline unit tests
streamlit run app/Home.py            # the app (Playground + Dashboard)
uvicorn api:app --reload             # optional API; open http://127.0.0.1:8000/docs
```
Full pipeline order for the project: `scripts/build_dataset.py` → `scripts/baselines.py` → `scripts/finetune.py` (Colab) → set `BLOCK_T` in `config.py` → `scripts/run_scripted.py` → deploy (`SPACE_README.md`) → `scripts/evaluate.py`.

## Results
All numbers are on the held-out **test split** (408 rows), used once by `scripts/evaluate.py`. Thresholds were tuned on validation only. Raw files and charts are in `results/`.

**Exp 1: model comparison** (classification threshold 0.5)

| model | accuracy | precision | recall | F1 | FPR |
|---|---|---|---|---|---|
| rules | 0.6985 | 1.0000 | 0.4029 | 0.5744 | 0.0000 |
| tfidf_logreg | 0.9412 | 1.0000 | 0.8835 | 0.9381 | 0.0000 |
| protectai_deberta (zero-shot) | 0.8946 | 0.9055 | 0.8835 | 0.8943 | 0.0941 |
| **muril (fine-tuned)** | 0.9534 | 0.9561 | 0.9515 | **0.9538** | 0.0446 |

**Exp 2: language gap** (F1)

| model | English | Hindi/Hinglish | gap |
|---|---|---|---|
| rules | 0.5923 | 0.5000 | 0.092 |
| tfidf_logreg | 0.9487 | 0.8947 | 0.054 |
| protectai_deberta | 0.9329 | 0.7660 | 0.167 |
| **muril** | 0.9512 | **0.9639** | -0.013 |

The English-only ProtectAI model loses 17 F1 points on Hindi/Hinglish; MuRIL shows no gap.

**Exp 3: layer ablation** (200 random test prompts, full pipeline with `BLOCK_T = 0.90`, LLM judge disabled via `--no-judge`, chatbot call skipped)

| config | attacks caught % | safe wrongly blocked % | mean latency ms | p95 latency ms |
|---|---|---|---|---|
| full (rules + classifier) | 91.1 | 0.9 | 146.8 | 537.9 |
| without rules | 91.1 | 0.9 | 94.5 | 318.4 |
| without classifier (rules only) | 43.3 | 0.0 | 0.3 | 1.5 |

**Honest reading of the results**
- MuRIL wins on overall F1 (+0.016 over TF-IDF) and clearly on Hindi/Hinglish (+0.07), but TF-IDF is a strong baseline with a lower false-positive rate on this test set. The dataset is small (2,716 rows) and partly machine-translated, so differences of a point or two are within noise.
- The rules add no extra catches once the classifier is on, but they are cheap and explainable; the classifier is what carries detection.
- The judge layer was not measured in Exp 3 (API quota). Fail-closed behaviour is covered by unit tests.
- Demo run (`results/scripted_results.csv`): with the shield off, 7 of 20 scripted attacks leaked a secret; with it on, 18 of 20 were blocked and 0 of 3 safe prompts were. The demo bot's system prompt was deliberately weakened (no "never reveal" sentence) so attacks can succeed.

## Links
- Live demo: https://promptshield-8my9icprhke5ntl3afinad.streamlit.app/
- Dataset: `GEET3001/promptshield-data` (private) · Model: `GEET3001/promptshield-muril` (private) · Dataset card: `data/README.md`
- Viva preparation: `docs/viva.md`

## Scope
Regex PII (no Presidio), one fine-tuned model plus baselines, single-process app. Out of scope: indirect injection, garak, HackAPrompt.

## Team
_(add names)_

## Licence
MIT
