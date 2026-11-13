# Darija Language Identification with fastText

A fast classifier that tells whether an Arabic-script text is **Moroccan Darija** (`ary`) or **another Arabic dialect** (`other`). It is typically the first step of a Darija data pipeline: before training an LLM, you filter scraped web and social media text to keep only Darija.

> Original notebook by the HackAI 2026 team, dataset [`atlasia/Darija-LID`](https://huggingface.co/datasets/atlasia/Darija-LID). I fixed two silent bugs, made it run on Windows, and added a grid search.

## Results (test set, 53,226 texts)

| Model | F1 Darija | F1 other | Accuracy |
|---|---|---|---|
| Notebook defaults | 0.99 | 0.98 | 0.99 |
| fastText autotune | 0.99 | 0.98 | 0.99 |
| **Grid search (mine)** | **0.9939** | **0.9850** | **0.9913** |

Best parameters: `lr=0.1`, `epoch=15`, `wordNgrams=2`, character n-grams 2 to 5 (`minn=2`, `maxn=5`). Character n-grams help with the many spelling variants of Darija.

The final model is retrained with `bucket=200000` and compressed with fastText quantization: `darija_lid.ftz`, **6.6 MB**, F1 0.9936 (no loss from compression). It is not committed (`*.ftz` is git-ignored): it is published on the Hugging Face Hub: **[JihaneJra/darija-lid-fasttext](https://huggingface.co/JihaneJra/darija-lid-fasttext)**.

## Pipeline

1. Load `atlasia/Darija-LID` (train / test).
2. Preprocess: remove URLs, digits, Latin letters, emojis and punctuation, keep Arabic text.
3. Explore: text length per class, most frequent words, Arabic word clouds.
4. Write fastText files (`__label__ary <text>` per line) and validate their format.
5. Train a supervised fastText model, evaluate with precision / recall / F1 and a confusion matrix.
6. Tune: fastText autotune, then a custom grid search on a validation split.

## What I fixed

| Problem | Why it matters | Fix |
|---|---|---|
| `to_csv(sep=' ')` wrapped every text in quotes (`"بابا بابا…"`) | fastText read the quotes as part of the first and last words | Write `label text` lines directly |
| **Validation leak**: the autotune validation set was also inside the training file | The tuning was scored on data the model had already seen | Train on `data_train_split.txt`, validate on `data_val.txt` |
| `pip install fasttext` fails on Windows (needs Visual Studio to compile) | | Install `fasttext-wheel` (same library, prebuilt) |
| fastText's `predict("one text")` crashes with numpy 2 | | Small compatibility patch after the import |
| `datasets` 5 pulls `huggingface-hub` 2, which breaks `transformers` 4 | Would break the other notebooks | Pinned `datasets<5` |
| The custom grid search cell was empty (`...`) | | 16 combinations scored on validation; the best one is retrained and evaluated once on test |
| The saved model would be ~850 MB (default `bucket` of 2M with character n-grams); a first save was truncated when the disk was full | A corrupted model answers "other" for everything | `bucket=200000` + quantization: a 6.6 MB `.ftz` file |

## Run it

CPU only, no API key. Training takes seconds; autotune about 5 minutes; the grid search a few minutes.

## Challenge questions

- **Which metric matters most?** For filtering a Darija corpus, **precision on `ary`** (do not let other dialects in) usually matters more than recall; F1 balances both.
- **Another architecture?** A fine-tuned multilingual encoder (e.g. a BERT-style model) would likely be a bit more accurate, but much slower and heavier than fastText.
- **How to improve?** Character n-grams (done), more and more diverse data, handling Arabizi (Darija in Latin letters, currently removed by the preprocessing).
