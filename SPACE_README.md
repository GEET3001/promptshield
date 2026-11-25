Paste this YAML header at the very top of the Space's own README.md (replace the file's existing header):

```yaml
---
title: PromptShield
emoji: 🛡️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 8501
pinned: false
---
```

## Deployment clicks (do these on huggingface.co)
1. Profile picture → **New Space** → name `promptshield`, SDK **Docker** (Blank), visibility **Public** → Create.
2. Space page → **Files** tab → **Add file → Upload files**. Upload everything from the repo EXCEPT `.env`, `.venv`, `.git`, `data/*.csv`, `results/*.tmp`. Keep the folders `app/`, `shield/`, `demo/`.
3. Open the Space's `README.md` → Edit → replace its header with the YAML above → Commit.
4. **Settings → Variables and secrets → New secret**, add all five, one by one:
   `GEMINI_API_KEY`, `GROQ_API_KEY`, `HF_TOKEN` (read access to your private model repo is enough), `ADMIN_CODE`, `CANARY`.
5. Before uploading, make sure `config.py` has your tuned `BLOCK_T` and that the model repo `GEET3001/promptshield-muril` exists.
6. Watch the **Logs** tab until it says the app is running (first build takes ~10 minutes; first model load ~1 minute).
7. Open the Space URL on your phone and run the 20 attacks from `demo/scripted_attacks.csv`.
8. If the build fails, copy the last 20 log lines and use fix-up prompt F2.

The log database is stored in `/tmp` inside the container, so it resets whenever the Space restarts. That is fine for a demo.
