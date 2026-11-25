"""PromptShield home page. Run from the repo root:  streamlit run app/Home.py"""
import streamlit as st

st.set_page_config(page_title="PromptShield", page_icon="🛡️", layout="wide")
st.title("🛡️ PromptShield")
st.write(
    "PromptShield is a layered firewall that sits between users and an LLM chatbot and blocks "
    "prompt-injection, jailbreak and secret-leak attacks. Most detectors are trained on English only; "
    "ours adds a **MuRIL** classifier fine-tuned to catch **Hindi and Hinglish** attacks too."
)
st.subheader("What happens to every message")
st.markdown(
    "1. **PII masker** hides Aadhaar, PAN, phone numbers and emails\n"
    "2. **Rule filter** blocks known attack patterns (English, Hinglish, Hindi)\n"
    "3. **Classifier** (MuRIL) scores how likely the message is an attack\n"
    "4. **LLM judge** double-checks borderline scores (fails closed if it errors)\n"
    "5. **Chatbot** (Riverside Institute of Technology Help Desk) answers\n"
    "6. **Output guard** blocks replies that leak the secret code, token or system prompt\n"
    "7. **Log** stores the masked prompt for the dashboard"
)
st.info("Open **Playground** in the sidebar to attack the bot with the shield on and off, "
        "and **Dashboard** to see what was blocked.")
st.caption("Source code and report: see the project README.")
