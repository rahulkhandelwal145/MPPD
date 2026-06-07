"""Phase 4 — quote extraction + statement classification (Groq LLM agent).

Two LLM calls per article:
  1. ``extract_quotes`` — pull direct quotes attributed to the MP (cheap).
  2. ``classify_statement`` — classify one quote into the A/B/C/D/E framework.

Display feature only — does NOT contribute to any score. Political opinions
are always category E. When in doubt, or confidence < 70, force E.
"""

import json
import re
import time

import httpx
from groq import Groq, RateLimitError
from loguru import logger

from backend.core.config import settings

_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)(m)?(\d+)?s")
_FENCE_RE = re.compile(r"```[a-z]*\n?")

VALID_CATEGORIES = {
    "A1", "A2", "A3", "A4", "A5",
    "B1", "B2", "B3", "B4", "B5",
    "C1", "C2", "C3",
    "D1", "D2", "D3", "D4", "D5",
    "E",
}

# Categories requiring a documented data source — without one we downgrade to E.
_DATA_REQUIRED = {"B1", "B2", "B3", "B4", "B5", "C1"}

_groq_client: Groq | None = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


def _call_groq(system: str, user: str, max_tokens: int, model: str | None = None) -> str:
    response = _get_groq().chat.completions.create(
        model=model or settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def _call_ollama(system: str, user: str) -> str:
    """Local Ollama fallback. format=json forces a valid JSON object."""
    resp = httpx.post(
        f"{settings.ollama_base_url}/api/chat",
        json={
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
            "keep_alive": "30m",
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def _call_llm(system: str, user: str, max_tokens: int = 800, model: str | None = None) -> str:
    if settings.llm_provider == "ollama":
        return _call_ollama(system, user)
    try:
        return _call_groq(system, user, max_tokens, model=model)
    except RateLimitError as e:
        logger.warning(f"Groq rate limit hit ({model or settings.groq_model}), falling back to Ollama: {e}")
        return _call_ollama(system, user)


def _strip_fences(raw: str) -> str:
    if raw.startswith("```"):
        raw = _FENCE_RE.sub("", raw).replace("```", "").strip()
    return raw


def _sleep_for_rate_limit(err: RateLimitError) -> None:
    m = _RETRY_AFTER_RE.search(str(err))
    if m:
        minutes = float(m.group(1)) if m.group(2) == "m" else 0
        secs = float(m.group(1)) if not m.group(2) else float(m.group(3) or 0)
        wait = minutes * 60 + secs + 5
    else:
        wait = 65
    logger.warning(f"Rate limited, sleeping {wait:.0f}s...")
    time.sleep(wait)


# ─── Quote extraction ──────────────────────────────────────────────────────────

QUOTE_SYSTEM_PROMPT = (
    "You extract direct quotes attributed to a named Indian MP from a news "
    "article. Return only direct quotes — text inside quotation marks that is "
    "attributed to the MP (said/stated/claimed/told reporters/tweeted/posted). "
    "Never include paraphrased speech, reported speech without quotes, other "
    "people's quotes, or headlines. Return valid JSON only. No markdown."
)

QUOTE_EXTRACTION_PROMPT = """Extract all direct quotes attributed to {mp_name} from this article text.

Return JSON only:
{{
  "quotes": [
    {{
      "text": "exact quoted text",
      "attribution": "said/stated/claimed/etc",
      "context": "one sentence of surrounding context"
    }}
  ]
}}

If no direct quotes found return:
  {{"quotes": []}}

Article text:
{article_text}"""

MAX_QUOTES_PER_ARTICLE = 20


def extract_quotes(article_text: str, mp_name: str, attempt: int = 0) -> list[dict]:
    """Return a list of {text, attribution, context} dicts. Empty on failure."""
    if attempt >= 3:
        return []

    try:
        prompt = QUOTE_EXTRACTION_PROMPT.format(
            mp_name=mp_name,
            article_text=article_text[:8000],
        )
        raw = _strip_fences(_call_llm(QUOTE_SYSTEM_PROMPT, prompt, max_tokens=1200, model=settings.groq_model))
        data = json.loads(raw)
        quotes = data.get("quotes", [])

        cleaned = []
        for q in quotes:
            text = (q.get("text") or "").strip().strip('"').strip("'").strip()
            if not text:
                continue
            cleaned.append({
                "text": text,
                "attribution": (q.get("attribution") or "").strip(),
                "context": (q.get("context") or "").strip(),
            })
        return cleaned[:MAX_QUOTES_PER_ARTICLE]

    except RateLimitError as e:
        _sleep_for_rate_limit(e)
        return extract_quotes(article_text, mp_name, attempt + 1)
    except (json.JSONDecodeError, KeyError, AttributeError, Exception) as e:
        logger.warning(f"Quote extraction attempt {attempt + 1} failed: {e}")
        return extract_quotes(article_text, mp_name, attempt + 1)


# ─── Classification ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a civic accountability assistant for India.
You classify statements made by Indian MPs.

You measure statements against:
  - Indian Constitution (specific articles)
  - Scientific consensus (WHO, ICMR, peer-reviewed)
  - Government's own documented data (NSSO, CMIE, RBI)

CRITICAL DIRECTION TEST: Before flagging A/B/C, ask yourself:
  Is the MP PERSONALLY EXPRESSING this view — or are they REPORTING,
  OPPOSING, DEFENDING, or CRITICISING it?
  Only flag if the MP is the SOURCE of the problematic view.
  If the MP is defending rights, opposing discrimination, or criticising
  a policy for harming a group -> that is NOT A/B/C, that is D or E.

You do NOT make political judgments.
Legitimate political opinions are always category E.
When in doubt classify as E.
Low confidence means classify as E.
Return valid JSON only. No markdown."""

CLASSIFICATION_PROMPT = """Classify this statement made by an Indian MP.

MP: {mp_name}
Statement: "{statement}"
Context: {context}
Source: {source}
Date: {date}

Categories:
  A1: Sexist/Anti-women (Articles 14,15,21)
       ONLY if the MP is personally demeaning/excluding women.
       Announcing women's reservation or defending women's rights -> E or D.
  A2: Casteist/Discriminatory (Articles 15,17,46)
       ONLY if the MP is personally asserting caste superiority or exclusion.
       Criticising another party's caste record -> E (political attack).
  A3: Communally divisive (Articles 14,15,25,51A-e)
  A4: Homophobic/Transphobic (Article 21)
       ONLY if the MP personally demeans LGBTQ+ persons.
       Opposing a bill that restricts trans rights -> NOT A4, classify E or D.
  A5: Anti-disabled/Ageist (RPWD Act, Article 41)
  B1: Medical pseudoscience (Article 51A-h, ICMR/WHO)
  B2: Climate/environment denial (Article 51A-g-h)
  B3: Historical revisionism as fact (Article 51A-h)
  B4: Vaccine/health denial (Article 51A-h, WHO)
  B5: Economic reality denial (NSSO/CMIE/RBI data)
  C1: Religious pseudoscience (Article 51A-h)
  C2: Theocratic statement (Preamble, Articles 25-28)
  C3: Religious incitement (Article 51A-e, IPC 153A)
  D1: Constructive — data-backed advocacy
  D2: Constructive — specific policy demand
  D3: Constructive — vulnerable group advocacy
  D4: Constructive — accountability demand
  D5: Constructive — evidence-based position
  E:  Political opinion — do not flag

Return JSON only. No explanation. No markdown.
{{
  "category":               "A1|A2|...|E",
  "speaker_is_mp":          true or false,
  "constitutional_anchor":  "Article X" or null,
  "data_contradicted":      "CMIE Q3 2025" or null,
  "reason":                 "one sentence, factual only",
  "confidence":             int 0-100
}}

speaker_is_mp: Is the MP personally and directly expressing this view in their
own voice? Answer false if the MP is describing, reporting, quoting, or
criticising a view held by someone else (another party, person, or government).

Rules:
  - confidence < 70 -> force category to E
  - speaker_is_mp false + category A/B/C -> always E (the MP is not the source
    of the problematic view; they are describing or criticising someone else)
  - DIRECTION RULE: Only flag A if the MP's own words demean or exclude a
    group. Reporting or criticising someone else's discrimination -> E or D.
  - Parliamentary procedure complaints (Speaker bias, time allocation) -> always E
  - Defending a group's rights or opposing a discriminatory bill -> D3 or E, never A
  - Personal faith -> always E
  - B or C categories require specific data source in data_contradicted
  - reason is factual, never opinionated
  - If unsure -> E"""


def classify_statement(
    statement: str,
    context: str,
    mp_name: str,
    source: str,
    date: str,
    attempt: int = 0,
) -> dict | None:
    """Classify one quote. Returns a dict with category/anchor/reason/confidence,
    or None if all attempts fail. Always returns a valid category (E on doubt)."""
    if attempt >= 3:
        return None

    try:
        prompt = CLASSIFICATION_PROMPT.format(
            mp_name=mp_name,
            statement=statement,
            context=context or "",
            source=source,
            date=date,
        )
        raw = _strip_fences(_call_llm(SYSTEM_PROMPT, prompt, max_tokens=350, model=settings.groq_classification_model))
        result = json.loads(raw)

        # Force E if confidence too low.
        if int(result.get("confidence", 0) or 0) < 70:
            result["category"] = "E"

        category = result.get("category")
        if category not in VALID_CATEGORIES:
            result["category"] = "E"
            category = "E"

        # If the MP is not personally expressing the view (speaker_is_mp=false),
        # they are reporting or criticising someone else — not a flag-worthy source.
        if not result.get("speaker_is_mp", True) and category[0] in ("A", "B", "C"):
            result["category"] = "E"
            category = "E"

        # B/C claims must cite a documented source, else they're just opinion.
        if category in _DATA_REQUIRED and not (
            result.get("data_contradicted") or result.get("constitutional_anchor")
        ):
            result["category"] = "E"

        result.setdefault("constitutional_anchor", None)
        result.setdefault("data_contradicted", None)
        result.setdefault("reason", "")
        result["confidence"] = int(result.get("confidence", 0) or 0)
        return result

    except RateLimitError as e:
        _sleep_for_rate_limit(e)
        return classify_statement(statement, context, mp_name, source, date, attempt + 1)
    except (json.JSONDecodeError, ValueError, TypeError, Exception) as e:
        logger.warning(f"Classification attempt {attempt + 1} failed: {e}")
        return classify_statement(statement, context, mp_name, source, date, attempt + 1)
