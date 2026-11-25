"""Central settings for PromptShield. Every tunable value lives here.

Values marked  # CHECK  must be verified by the team against the provider docs.
Secrets are NEVER stored here: they come from the environment / .env file.
"""
import os
from pathlib import Path

try:  # load .env if python-dotenv is installed (it is, locally; optional in Colab)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"

# ---------------- accounts / models ----------------
HF_USERNAME = "GEET3001"
GEMINI_MODEL = "gemini-2.5-flash"          # CHECK: current free Gemini model name
GROQ_JUDGE_MODEL = "llama-3.1-8b-instant"  # CHECK: current free Groq model name
MURIL_BASE = "google/muril-base-cased"
PROTECTAI_MODEL = "protectai/deberta-v3-base-prompt-injection-v2"
# Where the shield loads the fine-tuned classifier from (HF repo id or a local folder).
CLASSIFIER_SOURCE = os.getenv("CLASSIFIER_SOURCE", f"{HF_USERNAME}/promptshield-muril")
DATASET_REPO = f"{HF_USERNAME}/promptshield-data"

# ---------------- thresholds ----------------
BLOCK_T = 0.85   # CHECK: placeholder. Replace with the value printed by scripts/finetune.py
JUDGE_T = 0.4    # p >= BLOCK_T -> block; JUDGE_T <= p < BLOCK_T -> ask the LLM judge
TARGET_FPR = 0.02  # false-positive target on safe validation prompts when picking BLOCK_T

# ---------------- layer on/off flags (evaluate.py flips these for the ablation) ----------------
USE_PII = True
USE_RULES = True
USE_CLASSIFIER = True
USE_JUDGE = True
USE_OUTPUT_GUARD = True
SKIP_LLM = False  # True = never call the chatbot LLM (used only by the ablation experiment)

# ---------------- misc ----------------
DB_PATH = os.getenv("DB_PATH", str(ROOT / "promptshield.db"))
MAX_CHARS = 2000
JUDGE_TIMEOUT_S = 10
REFUSAL = "Sorry, I can't help with that request."
PERSONA = "Riverside Institute of Technology Help Desk"
SEED = 42


def get_secret(name: str) -> str:
    """Read a secret from the environment; fail with a clear message if missing."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set. Copy .env.example to .env and fill it in.")
    return value


def get_admin_code() -> str:
    return get_secret("ADMIN_CODE")


def get_canary() -> str:
    return get_secret("CANARY")
