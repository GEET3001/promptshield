"""Dashboard over the SQLite request log."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from shield import log

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Dashboard")
st.button("🔄 Refresh")

choice = st.radio("Show requests where the shield was", ["Any", "ON", "OFF"], horizontal=True)

conn = log.connect()
df = pd.read_sql("SELECT * FROM requests ORDER BY id DESC", conn)
conn.close()
if choice != "Any":
    df = df[df["shield_on"] == (1 if choice == "ON" else 0)]

if df.empty:
    st.info("No requests logged yet. Use the Playground page first.")
    st.stop()

blocked = df[df["verdict"] == "blocked"]
c1, c2, c3 = st.columns(3)
c1.metric("Total requests", len(df))
c2.metric("% blocked", f"{100 * len(blocked) / len(df):.1f}%")
c3.metric("Avg latency (ms)", f"{df['latency_total_ms'].mean():.0f}")

left, right = st.columns(2)
with left:
    st.subheader("Blocks by layer")
    st.bar_chart(blocked["blocked_by"].value_counts())
with right:
    st.subheader("Blocks by attack type")
    st.bar_chart(blocked["attack_type"].fillna("unknown").value_counts())

st.subheader("20 latest blocked prompts (masked)")
st.dataframe(blocked.head(20)[["ts", "prompt_masked", "blocked_by", "attack_type", "risk_score"]],
             use_container_width=True)
