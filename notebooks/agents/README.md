# Multi-Tool AI Agent with LangGraph

A conversational AI agent built on an LLM (`openai/gpt-oss-120b`, served by [Groq](https://groq.com)) that can **reason** and **use external tools** to answer questions a plain LLM cannot handle: real-time data, recent information and exact calculations.

> Built during the **HackAI Hackathon 2026** (1337 AI), starting from the introductory agents notebook and extended with real tools, a security layer and a test suite.

---

## Why an agent?

A plain LLM has three main limitations:

| Limitation | Example | How the agent solves it |
|---|---|---|
| **Hallucination** | Invents a confident but wrong answer | Uses tools to fetch real data |
| **Knowledge cutoff** | Doesn't know today's weather | Calls a live weather API |
| **Unreliable math** | Gets multi-step arithmetic wrong | Delegates calculations to a calculator tool |

The agent runs a **Reason → Act → Observe** loop: the LLM decides which tool to call (from each tool's name and description), reads the result, and repeats until it can give a final answer.

```
        User question
              │
              ▼
    ┌──────────────────┐   needs a tool?   ┌─────────────┐
    │   LLM (Groq)     │ ────── yes ─────► │    Tool     │
    │  reason / plan   │ ◄──── result ──── │  (weather,  │
    └──────────────────┘                   │  calc, ...) │
              │ no                         └─────────────┘
              ▼
        Final answer          (memory saved per thread_id)
```

---

## Features

- 🌦️ **Real-time weather**: `real_city_weather` uses the free [Open-Meteo](https://open-meteo.com) API (geocoding + forecast, no API key). It returns conditions, temperature, feels-like temperature, humidity, wind and today's min/max. City names are looked up in English, then in French (e.g. `Marrakech`). If a city still isn't found, the tool returns a hint and the agent **retries with another spelling on its own** (e.g. `Benguerir` → `Ben Guerir`).
- 🧮 **Safe calculator**: `safe_calculator` replaces `eval()` with an evaluator built on Python's `ast` module. It accepts only numbers and arithmetic operators (`+ - * / // % **`, parentheses). It refuses function calls, variables and imports (no code injection through the LLM), as well as huge exponents (no freezing).
- 🔍 **Web search** (DuckDuckGo) and 📄 **scientific paper lookup** (arXiv).
- 🧠 **Conversation memory**: per-session memory with LangGraph's `InMemorySaver` and a `thread_id`.
- 🌍 **Multilingual**: a system prompt makes the agent answer in the user's language (French, English, Arabic or Moroccan Darija).
- 📊 **Observability**: every step (LLM calls, tool calls, results, tokens, latency) is traced in [LangSmith](https://smith.langchain.com).
- 🔐 **Secure configuration**: API keys are loaded from a git-ignored `.env` file with `python-dotenv`. They are never hard-coded in the notebook.

---

## Tech stack

| Component | Role |
|---|---|
| **LangChain** | Common interface for models and tools (`@tool`, `create_agent`) |
| **LangGraph** | Runs the agent loop and its memory (checkpointer) |
| **langchain-groq** | Connector to the Groq API (LLM inference) |
| **langchain-community** | Ready-made tools (DuckDuckGo, arXiv) |
| **Open-Meteo API** | Real-time weather data (no key) |
| **LangSmith** | Tracing and debugging of agent runs |
| **python-dotenv** | Loads the API keys from the `.env` file |

---

## Getting started

### 1. Get your API keys
- **Groq** (required, free): https://console.groq.com/keys
- **LangSmith** (optional): https://smith.langchain.com → Settings → API Keys

### 2. Configure your keys (`.env` file)
The keys are **never written in the notebook**. They are loaded from a `.env` file with [`python-dotenv`](https://pypi.org/project/python-dotenv/).

At the root of the repository, copy `.env.example` to `.env`, then fill in your keys:
```
GROQ_API_KEY=your_groq_key
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=hack_ai
```
If you have no LangSmith key, set `LANGSMITH_TRACING=false`.

> ⚠️ `.env` is listed in `.gitignore`, so your real keys are never committed. Only `.env.example` (without values) is shared.

### 3. Run the notebook
Open `01_llm_agents.ipynb` in VS Code or Jupyter (no GPU needed), then run the cells in order:
1. The install cell installs the libraries, including `python-dotenv`.
2. The configuration cell calls `load_dotenv()` and prints whether the Groq key was found.
3. `ChatGroq` reads the key with `os.getenv("GROQ_API_KEY")`.

> In VS Code, `.vscode/settings.json` also loads `.env` into the Jupyter kernel (`python.envFile`).
> On Google Colab, there is no `.env` file: use **Secrets** (🔑 icon) with `google.colab.userdata` instead.

---

## Notebook structure

1. **Concepts**: LLM limitations, what an agent is, the Reason → Act → Observe loop.
2. **Setup and model**: loading the keys from `.env`, then loading `gpt-oss-120b` through Groq.
3. **Basic tools**: calculator, dummy weather, DuckDuckGo search, arXiv.
4. **First agent**: `create_agent` with 4 tools, then a multi-tool question.
5. **Memory**: `InMemorySaver` and `thread_id`.
6. **Exercise (extensions)**:
   - real weather tool (Open-Meteo)
   - demonstration of the `eval()` risk, then the safe AST-based calculator
   - `agent_v2`: new tools, system prompt and memory
   - `ask()` helper, which shows the tools called and their arguments
   - test suite

---

## Tests

| # | Scenario | Expected behavior |
|---|---|---|
| 1 | Weather in two cities + temperature difference | 2 weather calls + 1 calculator call, with a spelling retry |
| 2 | "Bonjour, comment vas-tu ?" | **No tool called** |
| 3 | Weather question in Darija | Answer in Darija |
| 4 | Memory: tell your name and city, then ask again | Remembered within the same `thread_id`, unknown in a new one |
| 5 | Ask the calculator to run Python code | Refused |

Tool-level tests (outside the agent):

| Input | Output |
|---|---|
| `safe_calculator("2 + 2 * 3")` | `8` |
| `safe_calculator("1 / 0")` | `Error: division by zero` |
| `safe_calculator("__import__('os').getcwd()")` | `Error: unsupported element: Call` |
| `safe_calculator("2 ** 1000")` | `Error: exponent too large` |
| `real_city_weather("Ben Guerir")` | Current weather in Ben Guerir, Morocco |

---

## Limitations and possible improvements

- **Memory**: `InMemorySaver` is lost when the notebook restarts. Use `SqliteSaver` or `PostgresSaver` for persistent memory.
- **Web search**: DuckDuckGo can rate-limit requests. Use Tavily or Brave Search in production.
- **Non-determinism**: LLM answers and tool choices can vary between runs. An automated evaluation set would make this measurable.
- **Next steps**: a Gradio demo on Hugging Face Spaces, Darija NLP tools (e.g. through an MCP server), and a retrieval tool (RAG) over custom documents.

---

## Key concepts learned

- Tool calling: how an LLM picks a tool from its name, docstring and typed arguments
- Agent orchestration with LangGraph (reasoning loop, checkpointers, threads)
- Tool security: validating LLM-generated inputs instead of executing them
- Prompt engineering with system prompts
- Agent observability with LangSmith
- Secret management with environment variables (`.env`, `python-dotenv`, `.gitignore`)
