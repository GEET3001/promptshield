"""Baselines on the validation set: rules, TF-IDF + LogisticRegression, ProtectAI zero-shot.
Run:  python scripts/baselines.py        (needs data/train.csv and data/val.csv from build_dataset.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

import config
from metrics import score
from shield import rules


def predict_rules(texts):
    return [int(rules.check(t)[0]) for t in texts]


def fit_tfidf(train_df):
    """Character n-grams cope with spelling variants and with Hinglish better than word tokens."""
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2)
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=config.SEED)
    clf.fit(vec.fit_transform(train_df["text"]), train_df["label"])
    return lambda texts: clf.predict(vec.transform(texts)).tolist()


def predict_protectai(texts):
    """Zero-shot ProtectAI DeBERTa. The attack label name is read from the model config."""
    from transformers import pipeline
    pipe = pipeline("text-classification", model=config.PROTECTAI_MODEL, truncation=True, max_length=256)
    id2label = pipe.model.config.id2label
    attack_labels = {v for v in id2label.values() if str(v).upper() != "SAFE"}
    print("ProtectAI labels:", id2label, "-> attack:", attack_labels)
    out = pipe(list(texts), batch_size=4)
    return [int(o["label"] in attack_labels) for o in out]


def main():
    train = pd.read_csv(config.DATA_DIR / "train.csv")
    val = pd.read_csv(config.DATA_DIR / "val.csv")
    y, langs = val["label"], val["language"]
    rows = []
    rows.append({"model": "rules", **score(y, predict_rules(val["text"]), langs)})
    rows.append({"model": "tfidf_logreg", **score(y, fit_tfidf(train)(val["text"]), langs)})
    rows.append({"model": "protectai_deberta", **score(y, predict_protectai(val["text"]), langs)})
    out = pd.DataFrame(rows)
    config.RESULTS_DIR.mkdir(exist_ok=True)
    out.to_csv(config.RESULTS_DIR / "baselines_val.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
