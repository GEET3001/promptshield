"""Print results/*.csv as Markdown tables to paste into README.md. Run: python scripts/results_to_md.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

import config

for name in ("baselines_val", "exp1_models", "exp2_language", "exp3_ablation"):
    path = config.RESULTS_DIR / f"{name}.csv"
    if not path.exists():
        print(f"\n### {name}\n(not generated yet)")
        continue
    df = pd.read_csv(path)
    print(f"\n### {name}\n")
    print("| " + " | ".join(df.columns) + " |")
    print("|" + "---|" * len(df.columns))
    for _, row in df.iterrows():
        print("| " + " | ".join(str(v) for v in row) + " |")
