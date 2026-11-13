---
title: Darija Language ID
emoji: 🗣️
colorFrom: green
colorTo: red
sdk: gradio
app_file: app.py
pinned: false
short_description: Is this text Moroccan Darija or another Arabic dialect?
models:
- JihaneJra/darija-lid-fasttext
datasets:
- atlasia/Darija-LID
---

# Darija Language Identification

Type a sentence in Arabic script: the app tells whether it is **Moroccan Darija** or **another Arabic dialect**, with a confidence score.

- **Model**: [`JihaneJra/darija-lid-fasttext`](https://huggingface.co/JihaneJra/darija-lid-fasttext), a 6.6 MB fastText classifier
- **Results**: F1 0.994 (Darija), accuracy 0.991 on 53,226 test texts of [`atlasia/Darija-LID`](https://huggingface.co/datasets/atlasia/Darija-LID)
- **Code**: [github.com/jihanejra/Hackai-2026-darija](https://github.com/jihanejra/Hackai-2026-darija)

Built during the HackAI 2026 hackathon (1337 AI).

Limitation: Darija written in Latin letters (Arabizi, e.g. `wach nta mzyan`) is not supported.
