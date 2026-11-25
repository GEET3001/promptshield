# PromptShield dataset card

**Task:** binary classification of user prompts: `0` safe, `1` prompt-injection / jailbreak / leak attempt.
**Languages:** English, Hindi (Devanagari), Hinglish (Hindi in Roman script).
**Built by:** `python scripts/build_dataset.py` (seed 42, split 70/15/15 stratified on label and language).

## Columns
`text` (≤ 2000 chars) · `label` · `attack_type` (`direct_override`, `prompt_leak`, `roleplay_jailbreak`, `obfuscation`, `payload_split`, `language_switch`, `none`) · `language` (`en`/`hi`/`hinglish`) · `source`

## Sources
- `deepset/prompt-injections` (German rows removed)
- `Lakera/gandalf_ignore_instructions` (all attacks)
- `jackhhao/jailbreak-classification`
- `handwritten.csv`: team-written attacks and hard negatives
- `hard_negative`: ~200 template-generated safe prompts that contain words like "ignore", "rules", "password"
- `*+gemini`: English rows translated to Hindi/Hinglish with Gemini (50 reviewed by the team)

## Counts (paste the table printed by `build_dataset.py`)
```
(paste here)
```

## Limitations
- `attack_type` for external datasets is assigned by our own regex rules, so it is approximate.
- Hindi/Hinglish rows are machine-translated, not natural user text; a translation always stays in the same split as its English source.
- Translated attacks are labelled `language_switch`.
- Fictional campus domain only; no indirect (document-borne) injection.
