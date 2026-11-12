# Darija NLP MCP Server

mcp-name: io.github.afafelwafi/darija-mcp
<!-- mcp-name: io.github.afafelwafi/darija-mcp-->

A Model Context Protocol (MCP) server with tools for **Moroccan Darija** text and **Morocco-aware** everyday information (prayer times, weather, public holidays). It works with any MCP client: Claude Desktop, Cursor, smolagents, LangChain, etc.

> Original server by [afafelwafi](https://github.com/afafelwafi/darija-mcp) (HackAI 2026). This version was extended during the HackAI Hackathon 2026 (1337 AI) with 4 new tools, an improved dialect detector, a new resource, a new prompt and a stdio mode for desktop clients. See [Changes in this version](#changes-in-this-version).

---

## Tools

| Tool | What it does | Example |
|---|---|---|
| `latin_to_arabic` | Darija written in Latin letters and digits (Arabizi) → Arabic script | `l7rara bzaf f Marrakech daba` → `الحرارة بزاف ف مراكش دابا` |
| `transliterate` | Arabic script → Latin letters (Buckwalter-like, digits for ع/ح) | `سلام` → `slam` |
| `detect_dialect` | Darija vs Modern Standard Arabic, in Arabic **or** Latin script | `{"dialect": "darija", "confidence": 1.0, "script": "latin", "markers": ["wach", "bzaf"]}` |
| `clean_arabic` | Removes diacritics (harakat), tatweel and extra spaces | `مَرْحَبـــا` → `مرحبا` |
| `prayer_times` | Today's prayer times for a city (Aladhan API, official Moroccan method) | `prayer_times("Rabat")` |
| `city_weather` | Current weather for a city (Open-Meteo API), names in English or French | `city_weather("Marrakech")` |
| `moroccan_holidays` | Moroccan national public holidays for a year (Nager.Date API) | `moroccan_holidays(2026)` |
| `hijri_today` | Today's date in the Hijri calendar (Aladhan API) | `2 Jumādá al-ākhirah 1448 AH` |

All external APIs are free and need **no API key**. When an API is down, the tools return an error message instead of crashing, so the agent can react.

## Resources

| URI | Content |
|---|---|
| `darija://stopwords` | A Darija stopword list (Latin script) |
| `darija://greetings` | Common greetings in Latin and Arabic script, with their meaning |
| `darija://arabizi-table` | The Arabizi → Arabic table used by `latin_to_arabic` |

## Prompts

| Prompt | Purpose |
|---|---|
| `summarize_in_darija(text)` | Summarize a text in 3 sentences of Darija |
| `translate_to_darija(text, script)` | Translate a text into natural Darija, in Latin (`script="latin"`) or Arabic (`script="arabic"`) script |

---

## How the Darija tools work

**`latin_to_arabic`** is rule-based, with no model:
1. A **lexicon** of frequent words whose spelling can't be guessed by rules (`salam` → `سلام`, `chokran` → `شكرا`, `inchallah` → `إن شاء الله`, city names...).
2. **Digraphs**: `ch`/`sh` → ش, `kh` → خ, `gh` → غ, `ou` → و.
3. **Arabizi digits**: `2` → ء, `3` → ع, `5` → خ, `7` → ح, `8` → ه, `9` → ق. Pure numbers such as `2026` or `1337` are kept as they are.
4. **Vowels**: `a`/`i`/`o`/`u` become ا/ي/و (long vowels), `e` is dropped (short vowel).
5. **Definite article**: `l` + consonant at the start becomes ال (`lkhedma` → `الخدمة`), and a final consonant + `a` becomes ة.
6. Doubled letters are written once, and the punctuation becomes Arabic (`?` → `؟`, `,` → `،`).

**`detect_dialect`** splits the text into **whole words** (so `nti` does not match inside a longer word), then counts Darija markers in both scripts (`wach`/`واش`, `bzaf`/`بزاف`, `dyal`/`ديال`, `daba`/`دابا`...) and MSA markers (`الذي`, `سوف`, `لكن`, `هذا`...).

---

## Run the server

```bash
pip install "fastmcp>=2.12,<3" "mcp>=1.24,<2"
```

**HTTP** (notebooks, remote clients), on `http://127.0.0.1:8765/mcp`:
```bash
python darija_server.py
```

**stdio** (Claude Desktop, Cursor: the client starts the server itself):
```bash
python darija_server.py --stdio
```

> `fastmcp` 3+ requires `mcp` 2.x, which the smolagents MCP client does not support yet: keep both on the versions above.

### Claude Desktop / Cursor

Add the server to the client configuration (use absolute paths):

```json
{
  "mcpServers": {
    "darija-toolkit": {
      "command": "python",
      "args": ["C:/path/to/darija-mcp/darija_server.py", "--stdio"]
    }
  }
}
```

| Client | Configuration file |
|---|---|
| Claude Desktop (Windows) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop (macOS) | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` |

Restart the client completely after editing the configuration.

### From Python (smolagents)

```python
from smolagents.mcp_client import MCPClient

client = MCPClient({"url": "http://127.0.0.1:8765/mcp", "transport": "streamable-http"})
tools = {t.name: t for t in client.get_tools()}
print(tools["latin_to_arabic"](text="wach nta mzyan?"))   # واش نتا مزيان؟
```

---

## Changes in this version

| Change | Details |
|---|---|
| ✅ New tool `latin_to_arabic` | Arabizi → Arabic script (lexicon + rules) |
| ✅ New tool `prayer_times` | Aladhan API, Moroccan calculation method (`method=21`) |
| ✅ New tool `city_weather` | Open-Meteo API, English then French city names |
| ✅ New tool `moroccan_holidays` | Nager.Date API |
| 🔧 Improved `detect_dialect` | Whole-word matching instead of substrings, Darija markers in Arabic **and** Latin script, more markers, detected script in the output |
| 🔧 Improved `hijri_today` | Returns an error message instead of crashing when the API is down |
| ✅ New resource `darija://arabizi-table` | Exposes the transliteration table |
| ✅ New prompt `translate_to_darija` | Latin or Arabic script output |
| ✅ `--stdio` mode | For Claude Desktop and Cursor |
| 📝 README | Rewritten to describe the tools the server really exposes |

## Limitations

- `latin_to_arabic` is a heuristic: short vowels and some spellings can't be guessed (`l9adia` → `القاديا` instead of `القضية`). Words in the lexicon are always right.
- `detect_dialect` relies on marker words: a short text with no marker returns `unknown`.
- `moroccan_holidays` only covers fixed national holidays: religious holidays follow the lunar calendar and are not included.
- `pyproject.toml` still describes the original package layout (`src/darija_mcp`): it must be updated before publishing this version to PyPI under a new name.

## Security

The tools only read public APIs and have no side effects (no messages sent, no files written). As with any MCP server, only connect servers you trust to your AI clients.

## License

MIT License
