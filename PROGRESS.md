# PROGRESS

| Stage | Code written | Team action needed |
| --- | --- | --- |
| P1 Skeleton | ✅ | venv, `pip install -r requirements.txt`, fill `.env`, `python smoke_test.py`; check model names in `config.py` |
| P2 Dataset | ✅ | `python scripts/build_dataset.py`; add `data/handwritten.csv`; review `data/translation_check.csv`; `--push` |
| P3 Baselines | ✅ | `python scripts/baselines.py` |
| P4 Fine-tune | ✅ | run `scripts/finetune.py` in Colab; copy `BLOCK_T` into `config.py` |
| P5 Pipeline | ✅ | `uvicorn api:app --reload` → `/docs` |
| P6 Tests + demo | ✅ (8 offline tests pass) | `pytest -q`; `python scripts/run_scripted.py` (need ≥ 5 leaks with shield off) |
| P7 Streamlit | ✅ | `streamlit run app/Home.py` |
| P8 Deploy files | ✅ | follow `SPACE_README.md` |
| P9 Evaluation | ✅ | `python scripts/evaluate.py` (add `--no-judge` if API limits are tight) |
| P10 README + viva | ✅ | add results tables, demo link, team names |

P1 done: skeleton, config, requirements, smoke test: usage: __% (user fills)
P2 done: scripts/build_dataset.py + data/README.md: usage: __% (user fills)
P3 done: shield/rules.py, scripts/metrics.py, scripts/baselines.py: usage: __% (user fills)
P4 done: scripts/finetune.py (Colab): usage: __% (user fills)
P5 done: shield/* pipeline + api.py: usage: __% (user fills)
P6 done: tests/test_shield.py, demo/scripted_attacks.csv, scripts/run_scripted.py: usage: __% (user fills)
P7 done: app/Home.py + Playground + Dashboard: usage: __% (user fills)
P8 done: Dockerfile + SPACE_README.md: usage: __% (user fills)
P9 done: scripts/evaluate.py: usage: __% (user fills)
P10 done: README.md + docs/viva.md: usage: __% (user fills)
