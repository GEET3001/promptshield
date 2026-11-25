"""Fine-tune MuRIL for attack detection. Meant for a Colab T4 GPU.
Colab cells (Runtime > Change runtime type > T4 GPU):
  1) !git clone https://github.com/GEET3001/promptshield.git && %cd promptshield
  2) !pip install -q transformers datasets accelerate scikit-learn matplotlib python-dotenv
  3) import os; os.environ['HF_TOKEN']='<your HF write token>'
  4) !python scripts/finetune.py --from_hub --output_dir /content/muril_out --push
  5) copy the printed BLOCK_T and the "muril" table row back to Claude; the rest is automatic.
"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

import config
from metrics import score

ID2LABEL = {0: "SAFE", 1: "ATTACK"}
LABEL2ID = {"SAFE": 0, "ATTACK": 1}


def softmax_attack_prob(logits):
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    return (e / e.sum(axis=1, keepdims=True))[:, 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=str(config.DATA_DIR / "train.csv"))
    ap.add_argument("--val", default=str(config.DATA_DIR / "val.csv"))
    ap.add_argument("--output_dir", default="models/muril")
    ap.add_argument("--from_hub", action="store_true", help="load train/val from the private HF dataset repo")
    ap.add_argument("--push", action="store_true", help="upload the model to a private HF repo")
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from sklearn.metrics import f1_score, precision_recall_curve
    from transformers import (AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding,
                              Trainer, TrainingArguments, set_seed)

    set_seed(config.SEED)
    if args.from_hub:
        from datasets import load_dataset
        hub = load_dataset(config.DATASET_REPO, token=os.getenv("HF_TOKEN"))
        train_df, val_df = hub["train"].to_pandas(), hub["validation" if "validation" in hub else "val"].to_pandas()
    else:
        train_df, val_df = pd.read_csv(args.train), pd.read_csv(args.val)
    tok = AutoTokenizer.from_pretrained(config.MURIL_BASE)

    def to_ds(df):
        ds = Dataset.from_pandas(df[["text", "label"]].reset_index(drop=True))
        return ds.map(lambda b: tok(b["text"], truncation=True, max_length=256), batched=True)

    train_ds, val_ds = to_ds(train_df), to_ds(val_df)
    model = AutoModelForSequenceClassification.from_pretrained(
        config.MURIL_BASE, num_labels=2, id2label=ID2LABEL, label2id=LABEL2ID)

    def compute_metrics(p):
        return {"f1": f1_score(p.label_ids, p.predictions.argmax(-1))}

    # 10% of all training steps as warmup (newer transformers versions dropped warmup_ratio)
    epochs, batch = 4, 16
    warmup_steps = int(0.1 * epochs * -(-len(train_ds) // batch))
    targs = TrainingArguments(
        output_dir=args.output_dir, learning_rate=2e-5, per_device_train_batch_size=batch,
        per_device_eval_batch_size=32, num_train_epochs=epochs, weight_decay=0.01, warmup_steps=warmup_steps,
        eval_strategy="epoch", save_strategy="epoch", load_best_model_at_end=True,
        metric_for_best_model="f1", greater_is_better=True, save_total_limit=1,
        fp16=torch.cuda.is_available(), seed=config.SEED, report_to="none")
    trainer = Trainer(model=model, args=targs, train_dataset=train_ds, eval_dataset=val_ds,
                      data_collator=DataCollatorWithPadding(tok), compute_metrics=compute_metrics)
    trainer.train()
    best_dir = os.path.join(args.output_dir, "best")
    trainer.save_model(best_dir)
    tok.save_pretrained(best_dir)

    # ---- score the validation set ----
    logits = trainer.predict(val_ds).predictions
    prob = softmax_attack_prob(logits)
    y, langs = val_df["label"].values, val_df["language"].values
    pred = (prob >= 0.5).astype(int)
    row = {"model": "muril", **score(y, pred, langs)}
    config.RESULTS_DIR.mkdir(exist_ok=True)
    csv_path = config.RESULTS_DIR / "baselines_val.csv"
    table = pd.read_csv(csv_path) if csv_path.exists() else pd.DataFrame()
    table = pd.concat([table[table.get("model", pd.Series(dtype=str)) != "muril"], pd.DataFrame([row])])
    table.to_csv(csv_path, index=False)
    print(table.to_string(index=False))

    # ---- BLOCK_T: lowest threshold whose validation FPR is within the target ----
    safe_prob = prob[y == 0]
    block_t = next((float(t) for t in np.linspace(0.01, 0.99, 99) if (safe_prob >= t).mean() <= config.TARGET_FPR), 0.99)
    in_band = int(((prob >= config.JUDGE_T) & (prob < block_t)).sum())
    print(f"\nBLOCK_T = {block_t:.2f} (val FPR <= {config.TARGET_FPR:.0%}); "
          f"{in_band} of {len(val_df)} val rows fall in [JUDGE_T={config.JUDGE_T}, BLOCK_T) -> sent to the judge")

    # ---- PR curve + errors ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    prec, rec, _ = precision_recall_curve(y, prob)
    plt.figure(figsize=(5, 4)); plt.plot(rec, prec)
    plt.xlabel("Recall"); plt.ylabel("Precision"); plt.title("MuRIL precision-recall (val)"); plt.tight_layout()
    plt.savefig(config.RESULTS_DIR / "pr_curve.png", dpi=150); plt.close()
    errors = val_df.assign(pred=pred, prob=prob.round(4))
    errors = errors[errors["pred"] != errors["label"]]
    errors[["text", "label", "pred", "prob", "attack_type", "language"]].to_csv(
        config.RESULTS_DIR / "val_errors.csv", index=False)

    # ---- CPU latency over 200 prompts ----
    cpu_model = AutoModelForSequenceClassification.from_pretrained(best_dir).to("cpu").eval()
    sample = val_df["text"].head(200).tolist()
    start = time.perf_counter()
    with torch.no_grad():
        for text in sample:
            cpu_model(**tok(text, return_tensors="pt", truncation=True, max_length=256))
    latency = (time.perf_counter() - start) / max(len(sample), 1) * 1000
    print(f"Mean CPU latency: {latency:.1f} ms/prompt")

    if args.push:
        repo = f"{config.HF_USERNAME}/promptshield-muril"
        cpu_model.push_to_hub(repo, private=True, token=os.getenv("HF_TOKEN"))
        tok.push_to_hub(repo, private=True, token=os.getenv("HF_TOKEN"))
        print("Pushed to", repo)

    print(f"\nCopy into config.py:  BLOCK_T = {block_t:.2f}   (JUDGE_T stays {config.JUDGE_T}; "
          f"CLASSIFIER_SOURCE = '{config.HF_USERNAME}/promptshield-muril')")


if __name__ == "__main__":
    main()
