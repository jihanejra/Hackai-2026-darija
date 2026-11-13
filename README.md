# HackAI 2026 — Generative AI for Moroccan Darija

My work on the **HackAI Hackathon 2026** challenges (1337 AI): a series of notebooks covering the full generative AI stack, from data and LLM agents to fine-tuning, alignment, evaluation, red-teaming and deployment, applied to **Moroccan Darija**, a low-resource language.

The original notebooks come from the [HackAI 2026 challenges](https://github.com/1337-Artificial-Intelligence/HackAI-Challenges-2026). This repository contains my runs, bug fixes and extensions. Each folder README says exactly what I changed.

---

## Results at a glance

| Challenge | What I built or fixed | Result |
|---|---|---|
| [**LLM agents**](notebooks/agents/) | LangGraph agent with a real weather API, an AST-based safe calculator (replaces `eval()`), a multilingual system prompt (FR/EN/AR/Darija), memory and a test suite | 5/5 test scenarios pass (multi-tool, no-tool, Darija, memory, code injection refused) |
| [**MCP server**](notebooks/mcps/) | Extended the Darija MCP server from 4 to 8 tools: Arabizi → Arabic transliteration, prayer times, weather, Moroccan holidays; whole-word dialect detection in both scripts; stdio mode for Claude Desktop | All 8 tools tested through the MCP protocol |
| [**Darija language ID**](notebooks/language-lid/) | Fixed a validation leak and a quoting bug in the training files, added a grid search, published the compressed model on the [Hugging Face Hub](https://huggingface.co/JihaneJra/darija-lid-fasttext) | **F1 (Darija) = 0.994**, accuracy 0.991 on 53,226 test texts |
| [**RAG**](notebooks/rag/) | Docling + FAISS + reranker pipeline on the AtlasOCR paper, made to run on an 8 GB laptop without GPU (silent empty-document failure, out-of-memory crash, hanging loader, rate limits) | RAGAS: context precision 1.00, recall 0.24, faithfulness 0.38: retrieval finds relevant but too little context (baseline before improvements) |
| [**Evaluation & red-teaming**](notebooks/eval/) | Made the full eval stack run (dependency conflicts, removed model, Windows issues) | RAGAS judge catches a wrong answer (faithfulness 1.0 → 0.5); garak: Base64 injection succeeds 60–80% of the time; inspect Darija safety eval 3/3 |

## How the notebooks fit together

```
 DATA                    MODEL                     APPLICATION               QUALITY
 ─────                   ─────                     ───────────               ───────
 scraping, cleaning  ──► SFT + LoRA          ──►   RAG (documents)     ──►   evaluation
 synthetic data          DPO / ORPO                agents + tools            red-teaming
 language ID (filter)    GRPO (reasoning)          MCP servers               defenses
                                │
                                ▼
                         DEPLOYMENT: vLLM on Modal (API)
```

- **Data**: Darija has little labeled data, so we scrape, clean, filter (language ID) and generate it.
- **Model**: teach a base model to follow instructions (SFT), to prefer good answers (DPO/ORPO), and to reason (GRPO).
- **Application**: connect the model to documents (RAG), to tools (agents) and to any client through a standard protocol (MCP).
- **Quality**: measure what it knows, whether it hallucinates, and whether it can be attacked, then add defenses.

---

## Setup

```bash
git clone https://github.com/<your-username>/<this-repo>.git
cd <this-repo>
cp .env.example .env   # then fill in your own keys
```

| Key | Used by | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | agents | https://console.groq.com/keys |
| `LANGSMITH_API_KEY` (optional) | agents tracing | https://smith.langchain.com |
| `GEMINI_API_KEY` | MCP agent, evaluation | https://aistudio.google.com |

## Skills covered

- **LLM applications**: LangGraph agents, tool calling, Model Context Protocol (FastMCP, smolagents), RAG
- **Training**: SFT with LoRA/QLoRA, preference alignment (DPO, ORPO), GRPO with verifiable rewards
- **Evaluation & safety**: lm-evaluation-harness, RAGAS, LLM-as-a-judge, garak red-teaming, inspect-ai, prompt injection defenses
- **Classic NLP**: fastText classification, preprocessing Arabic text, hyperparameter search, avoiding data leakage
- **Engineering**: secret management (`.env`), dependency conflicts, Windows compatibility, serverless deployment (vLLM, Modal)
