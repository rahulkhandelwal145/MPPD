---
name: statement-agent-test-patterns
description: Key patterns and gotchas discovered when writing tests for statement_agent.py
metadata:
  type: project
---

Tests for `backend/agents/statement_agent.py` live in `backend/tests/test_statement_agent.py` (created 2026-06-14).

**Why:** Phase 4 statement classification has four hard guards that force category E. These are the most test-critical paths and are fully covered with parametrize.

**How to apply:** When extending these tests or writing tests for news_pipeline.py (the caller), rely on these patterns:

## Guard matrix (what forces category E)

| Guard | Condition | Note |
|---|---|---|
| 1 | `confidence < 70` | Boundary: exactly 70 is NOT E |
| 2 | `speaker_is_mp=False` AND category in A/B/C | D and E categories are unaffected |
| 3 | category in `_DATA_REQUIRED` (B1-B5, C1) AND no `data_contradicted` AND no `constitutional_anchor` | C2/C3 are NOT in `_DATA_REQUIRED` |
| 4 | category not in `VALID_CATEGORIES` | Case-sensitive: "a1" != "A1" → E |

## Singleton reset required

`_groq_client` is a module-level singleton. Always reset it between tests:

```python
@pytest.fixture(autouse=True)
def reset_groq_singleton():
    import backend.agents.statement_agent as sa
    sa._groq_client = None
    yield
    sa._groq_client = None
```

## Mocking strategy

- Patch `backend.agents.statement_agent._call_llm` (not the Groq client directly) for most tests — cleaner and avoids the singleton.
- For Ollama fallback tests, patch `_call_groq` and `_call_ollama` separately.
- `groq.RateLimitError` requires `message`, `response`, and `body` kwargs.

## _DATA_REQUIRED set

`{"B1", "B2", "B3", "B4", "B5", "C1"}` — NOT C2/C3. C2 (theocratic) and C3 (religious incitement) pass without a data source.

## settings fixture

`settings` is a Pydantic BaseSettings object loaded from .env — monkeypatch individual attributes rather than replacing the whole object.

## No async tests needed

All functions in statement_agent.py are synchronous (no `async def`). No `@pytest.mark.asyncio` needed.
