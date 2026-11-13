---
language:
- ar
- ary
library_name: fasttext
pipeline_tag: text-classification
tags:
- fasttext
- language-identification
- darija
- moroccan-arabic
- arabic-dialects
datasets:
- atlasia/Darija-LID
metrics:
- f1
- accuracy
---

# Darija Language Identification (fastText)

A lightweight [fastText](https://fasttext.cc) classifier that tells whether an Arabic-script text is **Moroccan Darija** (`ary`) or **another Arabic dialect** (`other`).

Typical use: filtering scraped web or social media text to keep only Darija before training or evaluating a language model.

- **Size**: 6.6 MB (quantized `darija_lid.ftz`), runs on CPU in milliseconds
- **Labels**: `__label__ary` (Moroccan Darija), `__label__other` (other Arabic dialects)
- **Training data**: [`atlasia/Darija-LID`](https://huggingface.co/datasets/atlasia/Darija-LID)
- **Built during**: the HackAI 2026 hackathon (1337 AI). Code: [github.com/jihanejra/Hackai-2026-darija](https://github.com/jihanejra/Hackai-2026-darija/tree/main/notebooks/language-lid)

## Results

Test split of `atlasia/Darija-LID` (53,226 texts):

| Class | Precision | Recall | F1 |
|---|---|---|---|
| `ary` (Darija) | 0.9924 | 0.9947 | **0.9936** |
| `other` | 0.9871 | 0.9814 | 0.9842 |
| **Accuracy** | | | **0.9909** |

## Usage

```python
import re
import types
import fasttext
import numpy as np
from huggingface_hub import hf_hub_download

# numpy 2 compatibility: fasttext calls np.array(..., copy=False) when predicting a single string
_np = types.ModuleType("numpy_compat"); _np.__dict__.update(np.__dict__)
_np.array = lambda obj, *args, copy=None, **kwargs: np.asarray(obj, *args, **kwargs)
fasttext.FastText.np = _np

model_path = hf_hub_download("JihaneJra/darija-lid-fasttext", "darija_lid.ftz")
model = fasttext.load_model(model_path)

def preprocess(text: str) -> str:
    # same preprocessing as during training
    text = re.sub(r"\W+", " ", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[a-zA-Z]", "", text)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", "", text)
    return text.lower().strip()

labels, probs = model.predict(preprocess("واش نتا مزيان؟ بزاف ديال الخدمة اليوم"), k=2)
print(labels, probs)   # ('__label__ary', '__label__other') [1.00001 0.00001]
```

Install with `pip install fasttext-wheel huggingface_hub` (`fasttext-wheel` is the prebuilt version of `fasttext`, which works on Windows too).

- Predict **one text at a time** to get the probabilities: with a list of texts, `fasttext-wheel` returns the top probability for every label (the top label itself is correct, so lists are fine for batch labeling).
- fastText adds `1e-5` to every probability, so values can slightly exceed 1.

## Training

- **Preprocessing**: remove URLs, digits, Latin letters, emojis and punctuation; keep Arabic script.
- **Hyperparameters** (grid search on a validation split, then retrained on the full training set): `lr=0.1`, `epoch=15`, `wordNgrams=2`, character n-grams `minn=2`, `maxn=5`, `dim=100`, `loss=softmax`, `bucket=200000`. Character n-grams help with the many spelling variants of Darija.
- **Compression**: fastText quantization (`cutoff=100000`, `retrain=True`), from about 120 MB to 6.6 MB, with no loss of F1 (0.9935 before, 0.9936 after).
- The validation split was kept separate from the training file used for tuning (no data leakage).

## Limitations

- **Arabic script only**: Arabizi (Darija written in Latin letters and digits, e.g. `wach nta mzyan`) is removed by the preprocessing, so it cannot be classified.
- **Binary**: it separates Darija from "other dialects" but does not tell which dialect the other texts are.
- Very short texts (one or two words) are less reliable: many words are shared across dialects.
- Results reflect the distribution of `atlasia/Darija-LID`; performance on other domains may be lower.
