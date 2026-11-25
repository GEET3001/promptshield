"""Attack playground: chat with the bot, toggle the shield, fire demo attacks."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from shield import classifier
from shield.pipeline import run

st.set_page_config(page_title="Playground", layout="wide")
st.title("Playground")


@st.cache_resource
def warm_up():
    """Load the classifier once per server process. If it fails, the judge covers for it."""
    try:
        classifier.load()
        return "loaded"
    except Exception as exc:
        return f"not loaded ({type(exc).__name__}); the judge will decide instead"


status = warm_up()
shield_on = st.toggle("Shield ON", value=True)
st.caption(f"Classifier: {status}")

# ---- sidebar: demo attacks (one per attack type, up to 5) + one safe prompt ----
demo = pd.read_csv(ROOT / "demo" / "scripted_attacks.csv")
attacks = demo[demo["attack_type"] != "none"].drop_duplicates("attack_type").head(5)
safe = demo[demo["attack_type"] == "none"].head(1)
st.sidebar.header("Try a demo prompt")
for _, row in pd.concat([attacks, safe]).iterrows():
    label = "✅ Safe: " if row["attack_type"] == "none" else f"⚠️ {row['attack_type']}: "
    if st.sidebar.button(label + row["text"][:35] + "…", key=row["text"]):
        st.session_state["pending"] = row["text"]

if "history" not in st.session_state:
    st.session_state["history"] = []

for msg in st.session_state["history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        res = msg.get("result")
        if res:
            if res["verdict"] == "blocked":
                st.error(f"Blocked by {res['blocked_by']}")
            else:
                st.success("Allowed")
            st.caption(f"Risk score: {res['risk_score']} | Attack type: {res['attack_type']} | "
                       f"Masked: {res['masked_entities']}")
            with st.expander("Per-layer latency (ms)"):
                st.json(res["latency_ms"])

prompt = st.chat_input("Type a message to the Help Desk bot…") or st.session_state.pop("pending", None)
if prompt:
    st.session_state["history"].append({"role": "user", "content": prompt})
    with st.spinner("Thinking…"):
        result = run(prompt, shield_on=shield_on)
    st.session_state["history"].append({"role": "assistant", "content": result["reply"], "result": result})
    st.rerun()
