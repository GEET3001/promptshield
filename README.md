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
Generate tables with `python scripts/results_to_md.py` and paste them here after running `scripts/evaluate.py`.

| Experiment | File |
| --- | --- |
| Exp 1: model comparison | `results/exp1_models.csv` |
| Exp 2: English vs Hindi/Hinglish gap | `results/exp2_language.csv`, `exp2_language.png` |
| Exp 3: layer ablation + latency | `results/exp3_ablation.csv`, `exp3_latency.png` |

_Results will be added after the evaluation run._

## Links
- Live demo: _(add Space URL)_
- Dataset: `GEET3001/promptshield-data` (private) · Model: `GEET3001/promptshield-muril` (private) · Dataset card: `data/README.md`
- Viva preparation: `docs/viva.md`

## Scope
Regex PII (no Presidio), one fine-tuned model plus baselines, single-process app. Out of scope: indirect injection, garak, HackAPrompt.

## Team
_(add names)_

## Licence
MIT
