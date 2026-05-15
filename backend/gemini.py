"""
Gemini API client using only Python's stdlib urllib.
Model: gemini-1.5-flash (fast, low cost, supports JSON mode).
"""

import json
import urllib.request
import urllib.error

API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

TIMEOUT = 45


def check_citation(
    api_key: str,
    main_sentence: str,
    footnote_text: str,
    source_text: str | None,
    source_name: str | None,
) -> dict:
    """
    Ask Gemini to evaluate whether the cited source supports the proposition.

    Returns a dict:
      {
        "proposition_support":   {"verdict": str, "explanation": str},
        "parenthetical_accuracy":{"verdict": str, "explanation": str},
        "pincite_accuracy":      {"verdict": str, "explanation": str},
        "overall": str,
        "confidence": str,
        "error": str | None,
      }
    """
    if not api_key:
        return _error_result("No Gemini API key provided.")

    source_block = (
        f"SOURCE TEXT (retrieved from {source_name}):\n{source_text}"
        if source_text
        else "SOURCE TEXT: Could not be retrieved automatically."
    )

    prompt = f"""You are a legal citation accuracy checker for law review articles.

MAIN TEXT — the proposition this footnote is cited to support:
\"\"\"{main_sentence}\"\"\"

FOOTNOTE (the citation):
\"\"\"{footnote_text}\"\"\"

{source_block}

Evaluate the following three things:

1. PROPOSITION SUPPORT: Does the cited source actually support the proposition stated in the main text above? Consider whether the source says what the author claims it says.

2. PARENTHETICAL ACCURACY: If the footnote contains a parenthetical — text in parentheses after the year, such as "(holding that...)" or "(stating that...)" — does it accurately and fairly describe what the source says? If there is no parenthetical, say so.

3. PINCITE ACCURACY: If the footnote includes a pincite (a specific page or section number, e.g. "at 495" or ", 495"), does that specific location in the source contain the relevant passage? If there is no pincite or insufficient source text to verify, say so.

Respond ONLY with a JSON object — no markdown, no explanation outside the JSON:
{{
  "proposition_support": {{
    "verdict": "Supports | Does not support | Cannot verify",
    "explanation": "one or two sentences"
  }},
  "parenthetical_accuracy": {{
    "verdict": "Accurate | Inaccurate | No parenthetical | Cannot verify",
    "explanation": "one or two sentences"
  }},
  "pincite_accuracy": {{
    "verdict": "Accurate | Inaccurate | No pincite | Cannot verify",
    "explanation": "one or two sentences"
  }},
  "overall": "one sentence summary",
  "confidence": "High | Medium | Low"
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }

    url = f"{API_URL}?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        return _error_result(f"Gemini API error {exc.code}: {body[:300]}")
    except Exception as exc:
        return _error_result(f"Network error: {exc}")

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
        result.setdefault("error", None)
        return result
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        return _error_result(f"Could not parse Gemini response: {exc}. Raw: {str(data)[:300]}")


def _error_result(msg: str) -> dict:
    blank = {"verdict": "Cannot verify", "explanation": msg}
    return {
        "proposition_support":    blank,
        "parenthetical_accuracy": blank,
        "pincite_accuracy":       blank,
        "overall": msg,
        "confidence": "Low",
        "error": msg,
    }
