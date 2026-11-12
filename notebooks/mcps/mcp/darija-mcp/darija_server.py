from fastmcp import FastMCP
from datetime import datetime
import re, unicodedata, json, urllib.request, urllib.parse

mcp = FastMCP("darija-toolkit")

# ─────────── HELPERS ───────────

def _get_json(url: str, params: dict | None = None, timeout: int = 10):
    """GET a JSON API (follows redirects)."""
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "darija-mcp"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

# words in Latin script (Arabizi) or Arabic script
_WORD_RE = re.compile(r"[a-z0-9']+|[؀-ۿ]+")

# Arabizi -> Arabic script. Digraphs first, then single letters.
# Digits are the usual Arabizi convention: 2=ء 3=ع 5=خ 7=ح 8=ه 9=ق
ARABIZI_DIGRAPHS = {"ch": "ش", "sh": "ش", "kh": "خ", "gh": "غ", "ou": "و", "th": "ث"}
ARABIZI_LETTERS = {
    "a": "ا", "b": "ب", "t": "ت", "j": "ج", "d": "د", "r": "ر", "z": "ز",
    "s": "س", "f": "ف", "q": "ق", "k": "ك", "l": "ل", "m": "م", "n": "ن",
    "h": "ه", "w": "و", "y": "ي", "i": "ي", "o": "و", "u": "و",
    "g": "ڭ", "v": "ڤ", "p": "ب", "x": "كس", "c": "ك",
    "2": "ء", "3": "ع", "5": "خ", "7": "ح", "8": "ه", "9": "ق",
    "e": "",  # short vowel, not written in Arabic script
}
_VOWELS = set("aeiou")

# frequent words whose spelling the rules can't guess (short vowels, fixed expressions)
ARABIZI_LEXICON = {
    "salam": "سلام", "slm": "سلام", "chokran": "شكرا", "choukran": "شكرا", "shokran": "شكرا",
    "marhba": "مرحبا", "mrhba": "مرحبا", "bslama": "بسلامة", "inchallah": "إن شاء الله",
    "nchallah": "إن شاء الله", "hamdolilah": "الحمد لله", "l7amdolilah": "الحمد لله",
    "smhli": "سمحلي", "smh": "سمح", "chwiya": "شوية", "bezzaf": "بزاف", "mra": "مرا",
    "rajel": "راجل", "drari": "دراري", "3ndi": "عندي", "ghda": "غدا", "lbare7": "البارح",
    "marrakech": "مراكش", "casa": "كازا", "rbat": "الرباط", "fes": "فاس", "tanja": "طنجة",
    "lmaghrib": "المغرب", "lmghrib": "المغرب", "nhar": "نهار", "lma": "الما",
}

# ─────────── TOOLS ───────────

@mcp.tool
def transliterate(text: str) -> str:
    """Convert Arabic script to Latin (Buckwalter-ish). Useful for logs."""
    table = str.maketrans({
        "ا":"a","ب":"b","ت":"t","ث":"th","ج":"j","ح":"7","خ":"kh","د":"d",
        "ذ":"dh","ر":"r","ز":"z","س":"s","ش":"sh","ص":"S","ض":"D","ط":"T",
        "ظ":"Z","ع":"3","غ":"gh","ف":"f","ق":"q","ك":"k","ل":"l","م":"m",
        "ن":"n","ه":"h","و":"w","ي":"y","ى":"a","ة":"a","ء":"a",
    })
    return unicodedata.normalize("NFKC", text).translate(table)

def _arabizi_word(word: str) -> str:
    # pure numbers (years, prices, "1337") are not Arabizi: keep them
    if word.isdigit():
        return word
    if word in ARABIZI_LEXICON:
        return ARABIZI_LEXICON[word]
    # "l" + consonant at the start is the definite article: lkhedma -> الخدمة, l7rara -> الحرارة
    article = len(word) > 2 and word[0] == "l" and word[1] not in _VOWELS | {"l"}
    if article:
        stem = _arabizi_letters(word[1:])
        # feminine nouns: final consonant + "a" -> ة
        if len(word) >= 5 and word[-1] == "a" and word[-2] not in _VOWELS:
            stem = stem[:-1] + "ة"
        return "ال" + stem
    return _arabizi_letters(word)

def _arabizi_letters(word: str) -> str:
    out, i = [], 0
    while i < len(word):
        pair = word[i:i + 2]
        if pair in ARABIZI_DIGRAPHS:
            out.append(ARABIZI_DIGRAPHS[pair]); i += 2; continue
        # doubled letter (shadda) or doubled vowel: write it once
        if i > 0 and word[i] == word[i - 1]:
            i += 1; continue
        out.append(ARABIZI_LETTERS.get(word[i], word[i])); i += 1
    return "".join(out)

@mcp.tool
def latin_to_arabic(text: str) -> str:
    """
    Convert Darija written in Latin letters and digits (Arabizi, e.g. "wach nta mzyan?",
    "l7rara", "3afak") to Arabic script. Heuristic: a lexicon of frequent words first, then
    rules: long vowels a/i/ou become ا/ي/و, 'e' is dropped, "l" + consonant is the article ال,
    digits follow the Arabizi convention (3=ع, 7=ح, 9=ق, 5=خ, 2=ء, 8=ه).
    Args:
        text: Darija text in Latin letters.
    """
    arabic = _WORD_RE.sub(lambda m: _arabizi_word(m.group(0)) if m.group(0).isascii() else m.group(0),
                          text.lower())
    # Arabic punctuation
    return arabic.replace("?", "؟").replace(",", "،").replace(";", "؛")

# Darija markers in both scripts; MSA markers in Arabic script
DARIJA_MARKERS = {
    "wach", "wash", "bzaf", "bzef", "ghadi", "kayn", "kayna", "makayn", "makaynch", "f7al",
    "kima", "dyal", "dial", "nta", "nti", "khouya", "khoya", "mashi", "machi", "daba", "3lach",
    "kifach", "chno", "chnou", "achno", "fin", "mzyan", "mzian", "bghit", "bghina", "safi",
    "wakha", "3afak", "hadchi", "hna", "lhih", "dakchi", "walo", "ila", "bach", "3la",
    "واش", "بزاف", "غادي", "كاين", "كاينة", "ماكاينش", "ديال", "نتا", "نتي", "خويا", "ماشي",
    "دابا", "علاش", "كيفاش", "شنو", "اشنو", "فين", "مزيان", "بغيت", "صافي", "واخا", "عافاك",
    "هادشي", "داكشي", "والو", "هنا", "باش",
}
MSA_MARKERS = {
    "إن", "لكن", "حيث", "سوف", "قد", "الذي", "التي", "الذين", "لأن", "هذا", "هذه", "ذلك",
    "ليس", "لم", "لن", "أيضا", "كيف", "ماذا", "لماذا", "أين", "يجب", "نحن", "أنت",
}

@mcp.tool
def detect_dialect(text: str) -> dict:
    """
    Detect whether a text is Moroccan Darija or Modern Standard Arabic (MSA).
    Works on Arabic script and on Latin script (Arabizi). Matches whole words only.
    Args:
        text: the text to analyse.
    Returns the dialect (darija / msa / unknown), a confidence score, the script
    (arabic / latin / mixed) and the marker words found.
    """
    words = _WORD_RE.findall(text.lower())
    darija = [w for w in words if w in DARIJA_MARKERS]
    msa = [w for w in words if w in MSA_MARKERS]
    has_arabic = any(not w.isascii() for w in words)
    has_latin = any(w.isascii() and not w.isdigit() for w in words)
    script = "mixed" if has_arabic and has_latin else "arabic" if has_arabic else "latin"
    d, a = len(darija), len(msa)
    if d == a == 0:
        return {"dialect": "unknown", "confidence": 0.0, "script": script, "markers": []}
    if d > a:
        return {"dialect": "darija", "confidence": round(d / (d + a), 2), "script": script, "markers": darija}
    return {"dialect": "msa", "confidence": round(a / (d + a), 2), "script": script, "markers": msa}

@mcp.tool
def clean_arabic(text: str) -> str:
    """Strip diacritics, tatweel, and redundant whitespace."""
    text = re.sub(r"[ً-ْٰـ]", "", text)
    return re.sub(r"\s+"," ", text).strip()

@mcp.tool
def hijri_today() -> str:
    """Today's Hijri date via Aladhan public API."""
    try:
        data = _get_json("https://api.aladhan.com/v1/gToH", {"date": datetime.now().strftime("%d-%m-%Y")})
        h = data["data"]["hijri"]
        return f'{h["day"]} {h["month"]["en"]} {h["year"]} AH'
    except Exception as e:
        return f"Error while fetching the Hijri date: {e}"

@mcp.tool
def prayer_times(city: str, country: str = "Morocco") -> dict:
    """
    Today's prayer times for a city (Aladhan API, official Moroccan calculation method).
    Args:
        city: city name, e.g. "Rabat", "Casablanca", "Fes".
        country: country name (default "Morocco").
    """
    try:
        data = _get_json("https://api.aladhan.com/v1/timingsByCity",
                         {"city": city, "country": country, "method": 21})["data"]
        t = data["timings"]
        return {
            "city": city,
            "date": data["date"]["readable"],
            "hijri": f'{data["date"]["hijri"]["day"]} {data["date"]["hijri"]["month"]["en"]} {data["date"]["hijri"]["year"]}',
            "timings": {k: t[k] for k in ("Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha")},
        }
    except Exception as e:
        return {"error": f"Could not get prayer times for '{city}': {e}"}

WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "rime fog",
    51: "light drizzle", 53: "drizzle", 55: "dense drizzle", 61: "light rain", 63: "rain",
    65: "heavy rain", 71: "light snow", 73: "snow", 75: "heavy snow", 80: "rain showers",
    81: "rain showers", 82: "violent rain showers", 95: "thunderstorm", 96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}

@mcp.tool
def city_weather(city: str) -> dict:
    """
    Current weather for a city (Open-Meteo API, no key needed): conditions, temperature,
    humidity, wind and today's min/max.
    Args:
        city: city name, e.g. "Marrakech" or "Ben Guerir". If not found, retry with another spelling.
    """
    try:
        # try English then French names (e.g. "Marrakech" is only found in French)
        for language in ("en", "fr"):
            geo = _get_json("https://geocoding-api.open-meteo.com/v1/search",
                            {"name": city, "count": 1, "language": language})
            if geo.get("results"):
                break
        if not geo.get("results"):
            return {"error": f"City '{city}' not found. Try another spelling (e.g. 'Ben Guerir')."}
        place = geo["results"][0]
        data = _get_json("https://api.open-meteo.com/v1/forecast", {
            "latitude": place["latitude"], "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min", "timezone": "auto", "forecast_days": 1,
        })
        cur, day = data["current"], data["daily"]
        return {
            "city": place["name"], "country": place.get("country", ""), "time": cur["time"],
            "conditions": WEATHER_CODES.get(cur["weather_code"], "unknown"),
            "temperature_c": cur["temperature_2m"], "humidity_pct": cur["relative_humidity_2m"],
            "wind_kmh": cur["wind_speed_10m"],
            "min_c": day["temperature_2m_min"][0], "max_c": day["temperature_2m_max"][0],
        }
    except Exception as e:
        return {"error": f"Could not get the weather for '{city}': {e}"}

@mcp.tool
def moroccan_holidays(year: int) -> dict:
    """
    Moroccan national public holidays for a given year (Nager.Date API).
    Religious holidays (Eid, Mawlid, Islamic New Year) follow the lunar calendar and are not included.
    Args:
        year: e.g. 2026.
    """
    try:
        days = _get_json(f"https://date.nager.at/api/v3/PublicHolidays/{year}/MA")
        return {
            "year": year,
            "holidays": [{"date": d["date"], "name": d["name"], "local_name": d["localName"]} for d in days],
            "note": "Religious holidays (Eid al-Fitr, Eid al-Adha, Mawlid...) are not included.",
        }
    except Exception as e:
        return {"error": f"Could not get the holidays for {year}: {e}"}

# ─────────── RESOURCES ───────────

@mcp.resource("darija://stopwords")
def stopwords() -> str:
    """The 1337AI Darija stopword list."""
    sw = ["bach","ghir","ghadi","kayn","kayna","wach","wash","bzaf","kifach",
          "fin","fach","9bel","mn","l","f","b","3la","m3a","bla","kol","kollchi"]
    return "\n".join(sw)

@mcp.resource("darija://greetings")
def greetings() -> str:
    """Common Darija greetings, transliterated + Arabic."""
    return json.dumps([
        {"latin":"salam","arabic":"سلام","meaning":"hello"},
        {"latin":"labas","arabic":"لاباس","meaning":"how are you"},
        {"latin":"bikhir","arabic":"بخير","meaning":"fine"},
        {"latin":"shokran","arabic":"شكرا","meaning":"thank you"},
    ], ensure_ascii=False)

@mcp.resource("darija://arabizi-table")
def arabizi_table() -> str:
    """The Arabizi (Latin letters + digits) -> Arabic script table used by latin_to_arabic."""
    return json.dumps({"digraphs": ARABIZI_DIGRAPHS, "letters": ARABIZI_LETTERS}, ensure_ascii=False)

# ─────────── PROMPTS ───────────

@mcp.prompt
def summarize_in_darija(text: str) -> str:
    """Summarize the given text in 3 sentences of Darija."""
    return f"Lkhad had nass w 3tini résumé f tlata jamals b darija:\n\n{text}"

@mcp.prompt
def translate_to_darija(text: str, script: str = "latin") -> str:
    """Translate a text (French, English or MSA) into natural Moroccan Darija, in Latin or Arabic script."""
    writing = "Arabic script" if script == "arabic" else "Latin letters with digits (Arabizi: 3, 7, 9)"
    return (f"Translate the following text into natural, everyday Moroccan Darija "
            f"(not Modern Standard Arabic). Write it in {writing}. Keep names and numbers unchanged.\n\n{text}")

if __name__ == "__main__":
    import sys
    # `python darija_server.py --stdio` for Claude Desktop / Cursor (they spawn the server),
    # otherwise HTTP for the notebook and remote clients
    if "--stdio" in sys.argv:
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8765)
