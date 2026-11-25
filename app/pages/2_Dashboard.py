"""Activity page: what the shield has blocked, read from the SQLite request log."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

import pandas as pd
import streamlit as st

import ui
from shield import log

st.set_page_config(page_title="Activity", page_icon="🛡️", layout="wide")
ui.inject_css()
st.markdown('<div class="ps-head"><h1>Activity</h1>'
            '<p>Every message sent to the assistant, with what the shield decided. Only masked text is stored.</p></div>',
            unsafe_allow_html=True)

col_a, col_b = st.columns([3, 1])
with col_a:
    choice = st.radio("Show requests where the shield was", ["Any", "On", "Off"], horizontal=True)
with col_b:
    st.button("Refresh", use_container_width=True)

conn = log.connect()
df = pd.read_sql("SELECT * FROM requests ORDER BY id DESC", conn)
conn.close()
if choice != "Any":
    df = df[df["shield_on"] == (1 if choice == "On" else 0)]

if df.empty:
    st.markdown('<div class="ps-empty">No requests yet. Ask the assistant something on the Home page, then come back.</div>',
                unsafe_allow_html=True)
    st.stop()

blocked = df[df["verdict"] == "blocked"]
c1, c2, c3 = st.columns(3)
c1.metric("Messages", len(df))
c2.metric("Blocked", f"{100 * len(blocked) / len(df):.0f}%")
c3.metric("Average time", f"{df['latency_total_ms'].mean() / 1000:.1f} s")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Where messages were stopped")
    if blocked.empty:
        st.caption("Nothing blocked yet.")
    else:
        st.bar_chart(blocked["blocked_by"].value_counts(), color="#0B7A75")
with right:
    st.subheader("What kind of attack")
    if blocked.empty:
        st.caption("Nothing blocked yet.")
    else:
        st.bar_chart(blocked["attack_type"].fillna("not identified").value_counts(), color="#B3261E")

st.subheader("Latest blocked messages")
st.dataframe(blocked.head(20)[["ts", "prompt_masked", "blocked_by", "attack_type", "risk_score"]]
             .rename(columns={"ts": "Time", "prompt_masked": "Message", "blocked_by": "Stopped by",
                              "attack_type": "Attack type", "risk_score": "Risk score"}),
             use_container_width=True, hide_index=True)
