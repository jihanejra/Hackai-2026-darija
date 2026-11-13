# Preference alignment: SFT → DPO, and ORPO (Qwen2.5-3B, Arabic)

Teaching a model to follow Arabic instructions (SFT), then to **prefer good answers over bad ones** (DPO), and comparing it with ORPO, a single-stage method that does both at once. QLoRA 4-bit with Unsloth on a free Kaggle T4.

> Original notebook by the HackAI 2026 team. We fixed it so the full pipeline actually runs, and ran it on Kaggle: [`01_dpo_ppo_orpo_alignment_kaggle.ipynb`](01_dpo_ppo_orpo_alignment_kaggle.ipynb) (with all outputs).

## Published models

| Model | Method | Link |
|---|---|---|
| Qwen2.5-3B-Instruct + LoRA | SFT, then DPO | [JihaneJra/qwen2.5-3b-arabic-sft-dpo-lora](https://huggingface.co/JihaneJra/qwen2.5-3b-arabic-sft-dpo-lora) |
| Qwen2.5-3B-Instruct + LoRA | ORPO (single stage, from the base model) | [JihaneJra/qwen2.5-3b-arabic-orpo-lora](https://huggingface.co/JihaneJra/qwen2.5-3b-arabic-orpo-lora) |

Both are LoRA adapters (about 30M trainable parameters, 0.96% of the 3.1B): load them on top of `unsloth/Qwen2.5-3B-Instruct-bnb-4bit`.

## Setup

| | |
|---|---|
| Base model | `unsloth/Qwen2.5-3B-Instruct-bnb-4bit` (4-bit), LoRA r=16 on all 7 projection layers |
| SFT data | 2,000 Arabic instructions from [Bactrian-X](https://huggingface.co/datasets/MBZUAI/Bactrian-X) |
| Preference data | 500 (prompt, chosen, rejected) triples from [Arabic-preference-data-RLHF](https://huggingface.co/datasets/FreedomIntelligence/Arabic-preference-data-RLHF) |
| Hardware | Kaggle, 1 × Tesla T4 (16 GB), fp16 |

## Results

### SFT (250 steps, 11 min)

Training loss **2.08 → 1.32** (mean 1.34 over the epoch): the model learns the instruction format and the style of the Arabic answers.

### DPO (63 steps, 10 min, β = 0.1)

| Step | Loss | rewards/accuracies | rewards/margins |
|---|---|---|---|
| 5 | 0.693 | 0.08 | 0.000 |
| 10 | 0.691 | 0.65 | 0.004 |
| 50 | 0.672 | 0.65 | 0.044 |
| 60 | 0.661 | **0.83** | **0.067** |

The loss starts at 0.693 = ln 2, the value of a model that cannot tell `chosen` from `rejected` apart. It then goes down, while the **share of pairs where the model prefers the chosen answer goes from 8% to 83%** (0.90 averaged over the last logged steps) and the **margin widens**. This is the expected sign that DPO works: accuracy up and margin widening. The margins are still small after a single short epoch.

### ORPO (63 steps, 7 min, from the base model)

| Step | Loss | rewards/accuracies | rewards/margins |
|---|---|---|---|
| 5 | 2.12 | 0.65 | 0.014 |
| 55 | 1.99 | 0.75 | 0.022 |
| 60 | 2.09 | 0.58 | 0.006 |

ORPO **barely moved** in 63 steps: the loss stays around 2.0–2.1, and the accuracy oscillates between 0.55 and 0.75. Two likely reasons:

- its learning rate (8e-6) is very low for LoRA, since ORPO also has to do the SFT part;
- this Unsloth version does not accelerate ORPO.

A fair comparison with SFT + DPO would need a higher learning rate (around 1e-4 with LoRA) and more steps.

### Before / after, on the same Arabic prompt

The prompt asks how an assistant should answer sensitive or controversial questions in a balanced way.

- **Base model**: answers as itself ("an assistant like me should...") with generic advice.
- **SFT + DPO**: a structured, numbered answer focused on the method (context, privacy, balanced viewpoints, reliable sources), closer to the instruction-dataset style.
- **ORPO**: close to the base model, consistent with its flat training curves.

This is one prompt, a qualitative check and not a benchmark. A proper comparison would use an evaluation set (for example with the tools of [`notebooks/eval`](../eval/)).

## What we fixed in the original notebook

| Problem | Fix |
|---|---|
| `trainer.train()` for SFT was commented out, so DPO started from a model that had never been fine-tuned | SFT runs |
| ORPO was trained on top of the DPO model, so the two methods could not be compared | ORPO starts from a fresh base model with new LoRA adapters |
| Models were pushed to the original author's account | Pushed to `HF_USERNAME`, with the token from Kaggle Secrets |
| `tokenizer=` argument (old TRL API); ORPO moved in recent TRL | `processing_class=`; ORPO imported from `trl.experimental` if needed |
| `datasets<3.0` pin conflicting with TRL | Removed: Unsloth installs compatible versions |
| Weights & Biases login required | `report_to="none"` |
| Kaggle gives 2 GPUs; Unsloth trains on one | `CUDA_VISIBLE_DEVICES=0` |
| The optional Zephyr 7B comparison downloads about 28 GB | Off by default (`RUN_ZEPHYR = False`) |
| `captureompare(...)` typo, missing `return_dict=True` in the chat helper | Fixed |

## Run it on Kaggle

1. **Settings → Accelerator → GPU T4 x2**. Not the P100: Unsloth needs compute capability 7.0 or more.
2. **Settings → Internet → On**.
3. **Add-ons → Secrets**: add `HF_TOKEN` (a Hugging Face token with Write access), then enable it for the notebook.
4. Set `HF_USERNAME` in the setup cell.
5. Run the install cell, then **Run → Restart & clear cell outputs**, then **Run All**. About 1 hour in total.
