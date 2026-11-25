"""Run the scripted demo attacks with the shield OFF and ON. Run: python scripts/run_scripted.py [--delay 2]"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

import config
from shield import guard
from shield.pipeline import run


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=1.0, help="seconds to wait between API calls")
    args = ap.parse_args()
    df = pd.read_csv(ROOT_DEMO)
    rows = []
    for _, r in df.iterrows():
        off = run(r["text"], shield_on=False)
        time.sleep(args.delay)
        on = run(r["text"], shield_on=True)
        time.sleep(args.delay)
        rows.append({"text": r["text"], "attack_type": r["attack_type"], "language": r["language"],
                     "leaked_off": guard.is_leak(off["reply"]), "blocked_on": on["verdict"] == "blocked",
                     "blocked_by": on["blocked_by"]})
        print(rows[-1]["attack_type"], "| leaked_off:", rows[-1]["leaked_off"], "| blocked_on:", rows[-1]["blocked_on"])
    out = pd.DataFrame(rows)
    config.RESULTS_DIR.mkdir(exist_ok=True)
    out.to_csv(config.RESULTS_DIR / "scripted_results.csv", index=False)
    atk = out[out["attack_type"] != "none"]
    print(f"\nAttacks that leaked with shield OFF: {int(atk['leaked_off'].sum())}/{len(atk)}")
    print(f"Attacks blocked with shield ON: {int(atk['blocked_on'].sum())}/{len(atk)}")
    print(f"Safe prompts wrongly blocked: {int(out[out['attack_type'] == 'none']['blocked_on'].sum())}")


ROOT_DEMO = config.ROOT / "demo" / "scripted_attacks.csv"

if __name__ == "__main__":
    main()
