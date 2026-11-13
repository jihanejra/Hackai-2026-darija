import os
import re
import types

import fasttext
import gradio as gr
import numpy as np
from huggingface_hub import hf_hub_download

# fasttext calls np.array(..., copy=False), which numpy 2 rejects when predicting a single string:
# give fasttext a numpy whose array() behaves like np.asarray()
_np_compat = types.ModuleType("numpy_compat")
_np_compat.__dict__.update(np.__dict__)
_np_compat.array = lambda obj, *args, copy=None, **kwargs: np.asarray(obj, *args, **kwargs)
fasttext.FastText.np = _np_compat

# The model is downloaded from the Hub repo below (set MODEL_REPO in the Space settings to override)
MODEL_REPO = os.getenv("MODEL_REPO", "JihaneJra/darija-lid-fasttext")
model = fasttext.load_model(hf_hub_download(MODEL_REPO, "darija_lid.ftz"))

LABELS = {"ary": "Moroccan Darija", "other": "Other Arabic dialect"}


def preprocess(text: str) -> str:
    # same preprocessing as during training
    text = re.sub(r"\W+", " ", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[a-zA-Z]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", "", text)
    return text.lower().strip()


def identify(text: str):
    clean = preprocess(text or "")
    if not clean:
        raise gr.Error("Please write a text in Arabic script (Darija written in Latin letters is not supported).")
    # one text at a time: with a list, fasttext-wheel returns the top probability for every label
    labels, probs = model.predict(clean, k=2)
    # fastText adds 1e-5 to each probability: clip back to [0, 1]
    return {LABELS[label.replace("__label__", "")]: min(float(prob), 1.0) for label, prob in zip(labels, probs)}


demo = gr.Interface(
    fn=identify,
    inputs=gr.Textbox(label="Text (Arabic script)", lines=3, rtl=True, placeholder="اكتب شي جملة هنا..."),
    outputs=gr.Label(label="Prediction", num_top_classes=2),
    title="Darija Language Identification",
    description=(
        "Is this text **Moroccan Darija** or **another Arabic dialect**? "
        "A 6.6 MB fastText classifier (F1 0.994 on 53k test texts), built during the HackAI 2026 hackathon."
    ),
    examples=[
        ["واش نتا مزيان؟ بزاف ديال الخدمة اليوم"],
        ["شنو كتدير دابا؟ بغيت نمشي للبحر غدا"],
        ["إزيك عامل إيه النهارده؟"],
        ["شو عم تعمل هلق؟ كيفك؟"],
        ["إن هذا الكتاب الذي قرأته مفيد جدا"],
    ],
    flagging_mode="never",
)

if __name__ == "__main__":
    demo.launch()
