# Model Context Protocol (MCP) — Darija toolkit

How to give an LLM tools through a **standard protocol** instead of writing one connector per app, then building and extending an MCP server for Moroccan Darija.

> Original notebook and server by the HackAI 2026 team (server by [afafelwafi](https://github.com/afafelwafi/darija-mcp)). I fixed the notebook so it runs locally, and extended the server from 4 to 8 tools.

## What MCP solves

Without a standard, every AI app (Claude Desktop, Cursor, your agent...) needs its own connector for every service: **N × M** integrations. With MCP, each service ships **one server** and each app implements **one client**: **N + M**.

```
Agent (smolagents + Gemini) ◄── MCP (HTTP) ──► darija-toolkit server ──► public APIs
   discovers the tools                             8 tools, 3 resources,     (Open-Meteo, Aladhan,
   and calls them by writing code                  2 prompts                  Nager.Date)
```

| Primitive | Controlled by | Example in this server |
|---|---|---|
| **Tools** | the model | `latin_to_arabic`, `detect_dialect`, `prayer_times` |
| **Resources** | the application | `darija://stopwords`, `darija://arabizi-table` |
| **Prompts** | the user | `summarize_in_darija`, `translate_to_darija` |

## What I added to the server

| Change | Details |
|---|---|
| ✅ `latin_to_arabic` | Arabizi → Arabic script: `l7rara bzaf f Marrakech daba` → `الحرارة بزاف ف مراكش دابا` (lexicon + rules: digits 3/7/9, digraphs, article ال, ة, Arabic punctuation) |
| ✅ `prayer_times` | Today's prayer times for a city (Aladhan API, official Moroccan method) |
| ✅ `city_weather` | Current weather (Open-Meteo), city names in English then French |
| ✅ `moroccan_holidays` | National public holidays for a year (Nager.Date) |
| 🔧 `detect_dialect` | Whole-word matching (no more `nti` matching inside longer words), Darija markers in Arabic **and** Latin script, detected script in the output |
| 🔧 `hijri_today` | Returns an error message instead of crashing when the API is down |
| ✅ `darija://arabizi-table` resource, `translate_to_darija` prompt | |
| ✅ `--stdio` mode | Lets Claude Desktop / Cursor start the server |

All APIs are free and need no key. Every tool was tested through a real MCP client. See the [server README](mcp/darija-mcp/README.md) for details and limitations.

## What I fixed in the notebook

| Problem | Fix |
|---|---|
| `smolagents` fails with `mcp` 2.x (`cannot import name 'streamablehttp_client'`) | Pinned `mcp>=1.24,<2` and `fastmcp>=2.12,<3` |
| A leftover `fastmcp-slim` package broke `fastmcp` 2 | The install cell uninstalls it |
| Health check ran before the server was ready | Wait until the server answers instead of a fixed 3 s sleep |
| `gemma-4-26b-a4b-it` returned errors 500 | The agent tries several Gemini models in order, with automatic retries |
| Local fallback model needed `accelerate` | Added to the install cell |
| `UnicodeDecodeError` reading the server file (Arabic) on Windows | `read_text(encoding="utf-8")` |
| The clone cell duplicated the repository | Only clones when the files are missing (Colab) |
| Keys | Loaded from `.env` |

New sections: **3.6** (demo of the new tools, directly and through the agent) and **3.7** (stop the server and free port 8765).

## Run it

Locally (no GPU), with `GEMINI_API_KEY` in `.env`. Skip section 4 unless you want to link your personal WhatsApp account to Claude Desktop (it needs Go, a C compiler on Windows, and a QR code scan).

> ⚠️ Free Gemini tiers are often out of quota (429) or overloaded (503). The notebook handles it, but you may need to retry later. Groq's free tier (8,000 tokens/minute) is too small for a multi-step `smolagents` agent.

## Key concepts

- **Tool calling vs code agents**: `smolagents.CodeAgent` writes Python that calls the tools (flexible, fewer steps, but needs a sandbox); a JSON tool-calling agent (LangGraph) only fills in arguments (safer, more predictable).
- **Security**: an MCP server with access to private data, exposed to untrusted content and able to send messages (like the WhatsApp server) is subject to the "lethal trifecta": prompt injection can exfiltrate data.
