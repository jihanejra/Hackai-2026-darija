# RAG pipeline on a scientific paper (AtlasOCR)

An end-to-end Retrieval-Augmented Generation pipeline that answers questions about a PDF (the [AtlasOCR paper](https://arxiv.org/abs/2604.08070), the first open-source Darija OCR model), then evaluates itself with RAGAS.

> Original notebook by the HackAI 2026 team. We made it run on Windows and on an 8 GB laptop without a GPU, and fixed several silent failures.

## Pipeline

```
PDF ──► Docling (parsing) ──► HybridChunker (64 tokens) ──► MiniLM embeddings ──► FAISS index
                                                                                     │
question ──► embedding ──► top-4 search ──► jina-reranker-v3 (top-2) ──► LLM (Groq, gpt-oss-120b) ──► answer
                                                                                                      │
                                         RAGAS: generated test questions + LLM-as-a-judge scoring ◄───┘
```

## Results

The paper gives 7 pages and 100 chunks. A RAGAS test set of 4 questions is generated automatically from the paper (2 single-hop, 2 multi-hop), and the judge is `gpt-oss-120b` on Groq:

| Metric | What it measures | Score |
|---|---|---|
| **context_precision** | Are the retrieved chunks relevant? | **1.00** |
| context_recall | Did retrieval find everything needed? | 0.24 |
| faithfulness | Is the answer supported by the retrieved chunks? | 0.38 |
| answer_relevancy | Does the answer address the question? | 0.22 |

**Reading the scores:** the retrieved chunks are relevant (precision 1.0), but they do not contain enough information (recall 0.24). 2 of the 4 test questions get "I do not know". The prompt tells the model to say so when the context is insufficient, so it does not hallucinate, but it cannot answer. The causes are on the retrieval side:

- chunks of only **64 tokens** (about 2 sentences) split the information;
- only the **top 2** chunks reach the LLM;
- a small, English-only embedding model.

With only 4 test questions, these scores are indicative, not a benchmark.

**Next step:** larger chunks (256 tokens), more retrieved chunks (top-10, then rerank to top-4), and a multilingual embedding model, comparing the RAGAS scores before and after.

## What we fixed

| Problem | Fix |
|---|---|
| `faiss-gpu-cu12` needs Linux + an NVIDIA GPU | `faiss-cpu` |
| `ragas` 0.4 forces `openai` 1.x, which breaks `litellm` (used by the MCP notebook) | Runs in the separate `hackai-eval` environment with `ragas` 0.2, the API this notebook uses |
| **Docling returned an empty document** (a model download failed silently), and the whole pipeline ran on nothing | A check that stops with a clear message if the converted document is empty |
| The kernel died (access violation) on an 8 GB machine during the PDF conversion | OCR turned off (an arXiv PDF already has a text layer: about 5× faster), conversion models freed from memory afterwards |
| arXiv dropped the connection during the conversion | The PDF is downloaded once and converted from the local file |
| The RAGAS document loader (`unstructured`) hung for 40 minutes, downloading NLTK data | `TextLoader` (the markdown is plain text) |
| `input()` blocks a non-interactive run | The question is written in the cell |
| The default loader pattern `*.md` would also load this README into the test set | Loads only `document.md` |
| Groq's free tier (8,000 tokens/minute) makes RAGAS fail with rate limits | `RunConfig(max_workers=2, max_retries=15)` |
| Writing `document.md` (Arabic characters) failed on Windows | UTF-8 encoding |
| The reranker in `bfloat16` on CPU | `float32` when there is no GPU |
| Key hard-coded in the notebook | `GROQ_API_KEY` from `.env` |

## Run it

Use the **Python (hackai-eval)** kernel (see [notebooks/eval/README.md](../eval/README.md)) and put `GROQ_API_KEY` in the `.env` at the root of the repository. No GPU is needed. It takes about 15 minutes on CPU: the PDF conversion takes about 1 minute, and RAGAS is the slowest part because of the Groq rate limit. The first run also downloads about 1.9 GB of models (Docling, the embeddings and the reranker).
