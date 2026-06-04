import json
import re
import time
from typing import Optional

import httpx
from groq import Groq, RateLimitError
from loguru import logger
from pydantic import BaseModel, ValidationError, field_validator

from backend.core.config import settings

_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)(m)?(\d+)?s")

_groq_client: Groq | None = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.groq_api_key)
    return _groq_client


def _call_groq(system: str, user: str) -> str:
    response = _get_groq().chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def _call_ollama(system: str, user: str) -> str:
    """Call a local Ollama model. format=json forces a valid JSON object."""
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
            # Keep the model resident in VRAM across the whole pipeline run
            # so there are no mid-run reloads between candidates.
            "keep_alive": "30m",
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def _call_llm(system: str, user: str) -> str:
    if settings.llm_provider == "ollama":
        return _call_ollama(system, user)
    return _call_groq(system, user)

SERIOUS_SECTIONS = {
    "302", "307", "376", "354", "364", "395", "396", "397",
    "120B", "124A", "153A", "295A", "420", "467", "468", "471",
}

SYSTEM_PROMPT = """You are a structured data extraction assistant.
You extract information from Indian MP election
affidavit pages and return valid JSON only.

Rules:
- Return ONLY a valid JSON object. No explanation.
  No markdown. No backticks. Just raw JSON.
- All rupee figures must be plain integers with no
  commas, symbols, or text. e.g. 28031732 not
  "Rs 28,03,17,321"
- If a field is not present in the text, use null
  for optional fields and 0 for counts.
- Do not invent data that is not in the text.
- criminal_cases must list each case as a separate
  object, not combined.
- has_conviction is true only if the text explicitly
  mentions "convicted" or "conviction".
- asset_history should include all prior election
  declarations visible in the text."""

EXTRACTION_PROMPT = """Extract all available data from this Indian MP
affidavit page and return it as JSON matching
this exact schema:

{{
  "total_criminal_cases": int,
  "criminal_cases": [
    {{
      "ipc_section": "string",
      "description": "string",
      "is_serious": bool
    }}
  ],
  "has_conviction": bool,
  "total_assets_rupees": int or null,
  "movable_assets_rupees": int or null,
  "immovable_assets_rupees": int or null,
  "total_liabilities_rupees": int or null,
  "asset_history": [
    {{
      "election": "string",
      "assets_rupees": int or null
    }}
  ],
  "self_income_rupees": int or null,
  "spouse_income_rupees": int or null,
  "education": "string or null"
}}

Mark is_serious as true for these IPC sections:
302, 307, 376, 354, 364, 395, 396, 397, 120B,
124A, 153A, 295A, 420, 467, 468, 471
and any offence with punishment of 5+ years.

Page text:
{page_text}

{error_context}"""

_FENCE_RE = re.compile(r"```[a-z]*\n?")


class CriminalCase(BaseModel):
    ipc_section: str
    description: str
    is_serious: bool = False


def _to_optional_int(v):
    """Coerce model output (which often returns rupee figures as floats or
    strings) to an int. Returns None for blanks/unparseable values."""
    if v is None or v == "":
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


class AssetHistoryEntry(BaseModel):
    election: str
    assets_rupees: Optional[int] = None

    @field_validator("assets_rupees", mode="before")
    @classmethod
    def _coerce_assets(cls, v):
        return _to_optional_int(v)


class AffidavitExtraction(BaseModel):
    total_criminal_cases: int = 0
    criminal_cases: list[CriminalCase] = []
    has_conviction: bool = False
    total_assets_rupees: Optional[int] = None
    movable_assets_rupees: Optional[int] = None
    immovable_assets_rupees: Optional[int] = None
    total_liabilities_rupees: Optional[int] = None
    asset_history: list[AssetHistoryEntry] = []
    self_income_rupees: Optional[int] = None
    spouse_income_rupees: Optional[int] = None
    education: Optional[str] = None

    @field_validator(
        "total_assets_rupees", "movable_assets_rupees", "immovable_assets_rupees",
        "total_liabilities_rupees", "self_income_rupees", "spouse_income_rupees",
        mode="before",
    )
    @classmethod
    def _coerce_optional_int(cls, v):
        return _to_optional_int(v)

    @field_validator("total_criminal_cases", mode="before")
    @classmethod
    def cases_non_negative(cls, v) -> int:
        return max(0, _to_optional_int(v) or 0)


def extract_affidavit(page_text: str, candidate_id: int) -> AffidavitExtraction | None:
    error_context = ""

    for attempt in range(3):
        try:
            prompt = EXTRACTION_PROMPT.format(
                page_text=page_text,
                error_context=error_context,
            )

            raw = _call_llm(SYSTEM_PROMPT, prompt)

            if raw.startswith("```"):
                raw = _FENCE_RE.sub("", raw).replace("```", "").strip()

            data = json.loads(raw)
            return AffidavitExtraction(**data)

        except (json.JSONDecodeError, ValidationError) as e:
            error_context = (
                f"Your previous response failed with: {e}. Fix it and try again."
            )
            logger.warning(
                f"Extraction attempt {attempt + 1} failed for candidate {candidate_id}: {e}"
            )

        except RateLimitError as e:
            # Parse "try again in Xm Ys" or "try again in X.Ys" from Groq's message
            msg = str(e)
            m = _RETRY_AFTER_RE.search(msg)
            if m:
                minutes = float(m.group(1)) if m.group(2) == "m" else 0
                secs = float(m.group(1)) if not m.group(2) else float(m.group(3) or 0)
                wait = minutes * 60 + secs + 5  # 5s buffer
            else:
                wait = 65
            logger.warning(f"Rate limited for candidate {candidate_id}, sleeping {wait:.0f}s...")
            time.sleep(wait)
            continue

        except Exception as e:
            logger.error(f"Unexpected error for candidate {candidate_id}: {e}")
            break

    logger.error(
        f"All extraction attempts failed for candidate {candidate_id}. Storing partial."
    )
    return None
