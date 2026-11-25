"""Final evaluation on data/test.csv (use once!). Run: python scripts/evaluate.py [--no-judge] [--delay 2]
Exp1 model comparison, Exp2 language gap, Exp3 layer ablation (+ latency), MuRIL confusion matrix.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix

import config
from baselines import fit_tfidf, predict_protectai, predict_rules
from metrics import score
from shield import classifier
from shield.pipeline import run

R = config.RESULTS_DIR


def exp1_and_2(train, test):
    y, langs, texts = test["label"].values, test["language"].values, test["text"].tolist()
    muril = [int(classifier.attack_probability(t) >= 0.5) for t in texts]
    preds = {"rules": predict_rules(texts), "tfidf_logreg": fit_tfidf(train)(texts),
             "protectai_deberta": predict_protectai(texts), "muril": muril}
    exp1 = pd.DataFrame([{"model": m, **score(y, p, langs)} for m, p in preds.items()])
    exp1.to_csv(R / "exp1_models.csv", index=False)
    exp2 = exp1[["model", "f1_en", "f1_hi_hinglish"]].assign(gap=lambda d: (d["f1_en"] - d["f1_hi_hinglish"]).round(4))
    exp2.to_csv(R / "exp2_language.csv", index=False)
    ax = exp2.set_index("model")[["f1_en", "f1_hi_hinglish"]].plot.bar(figsize=(7, 4), rot=15)
    ax.set_ylabel("F1"); ax.set_title("Language gap: English vs Hindi/Hinglish (test)")
    plt.tight_layout(); plt.savefig(R / "exp2_language.png", dpi=150); plt.close()
    cm = confusion_matrix(y, muril, labels=[0, 1])
    plt.figure(figsize=(4, 4)); plt.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        plt.text(j, i, int(v), ha="center", va="center")
    plt.xticks([0, 1], ["SAFE", "ATTACK"]); plt.yticks([0, 1], ["SAFE", "ATTACK"])
    plt.xlabel("Predicted"); plt.ylabel("True"); plt.title("MuRIL confusion matrix (test)")
    plt.tight_layout(); plt.savefig(R / "confusion_matrix_muril.png", dpi=150); plt.close()
    best = exp1.sort_values("f1", ascending=False).iloc[0]
    print(f"[Exp1] best model on test: {best['model']} (F1={best['f1']})")
    print(f"[Exp2] MuRIL F1 en={exp2.set_index('model').loc['muril', 'f1_en']} "
          f"hi/hinglish={exp2.set_index('model').loc['muril', 'f1_hi_hinglish']}")


def exp3(test, n, no_judge, delay):
    sample = test.sample(min(n, len(test)), random_state=config.SEED)
    configs = {"full": {}, "no_rules": {"USE_RULES": False},
               "no_classifier": {"USE_CLASSIFIER": False}, "no_judge": {"USE_JUDGE": False}}
    if no_judge:
        configs = {k: {**v, "USE_JUDGE": False} for k, v in configs.items() if k != "no_judge"}
    config.SKIP_LLM = True  # we measure blocking decisions only, so no chatbot calls are needed
    rows = []
    for name, overrides in configs.items():
        saved = {k: getattr(config, k) for k in overrides}
        for k, v in overrides.items():
            setattr(config, k, v)
        blocked, lat = [], []
        for text in sample["text"]:
            res = run(text, shield_on=True)
            blocked.append(res["verdict"] == "blocked")
            lat.append(res["latency_ms"]["total"])
            if delay:
                time.sleep(delay)
        for k, v in saved.items():
            setattr(config, k, v)
        blocked, labels = np.array(blocked), sample["label"].values
        rows.append({"config": name, "attacks_caught_pct": round(100 * blocked[labels == 1].mean(), 1),
                     "safe_wrongly_blocked_pct": round(100 * blocked[labels == 0].mean(), 1),
                     "latency_mean_ms": round(float(np.mean(lat)), 1), "latency_p95_ms": round(float(np.percentile(lat, 95)), 1)})
        print(f"[Exp3] {name}: {rows[-1]}")
    config.SKIP_LLM = False
    out = pd.DataFrame(rows)
    out.to_csv(R / "exp3_ablation.csv", index=False)
    ax = out.set_index("config")[["latency_mean_ms", "latency_p95_ms"]].plot.bar(figsize=(6, 4), rot=0)
    ax.set_ylabel("ms per request"); ax.set_title("Latency by pipeline configuration")
    plt.tight_layout(); plt.savefig(R / "exp3_latency.png", dpi=150); plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-judge", action="store_true", help="disable the LLM judge in Exp3 (saves API calls)")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between pipeline runs (API rate limits)")
    ap.add_argument("--n", type=int, default=200, help="prompts used in Exp3")
    args = ap.parse_args()
    R.mkdir(exist_ok=True)
    train, test = pd.read_csv(config.DATA_DIR / "train.csv"), pd.read_csv(config.DATA_DIR / "test.csv")
    exp1_and_2(train, test)
    exp3(test, args.n, args.no_judge, args.delay)


if __name__ == "__main__":
    main()
