from typing import TypedDict

from groq import AsyncGroq
from langgraph.graph import StateGraph, END
from loguru import logger

from backend.agent.sql_tool import execute_sql
from backend.agent.prompt import SCHEMA_CONTEXT, GENERATE_SQL_PROMPT, FORMAT_ANSWER_PROMPT
from backend.core.config import settings

MODEL = "llama-3.1-8b-instant"


class ChatState(TypedDict):
    question: str
    sql_query: str | None
    sql_result: list[dict] | None
    answer: str | None
    attempts: int
    error: str | None


def _client() -> AsyncGroq:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in .env")
    return AsyncGroq(api_key=settings.groq_api_key)


async def generate_sql_node(state: ChatState) -> dict:
    attempt = state.get("attempts", 0)
    logger.info("[chat] generate_sql | question='{}' attempt={}", state["question"], attempt)

    error_context = ""
    if state.get("error"):
        error_context = (
            f"Your previous query failed with this error: {state['error']}. "
            "Write a corrected query."
        )
        logger.warning("[chat] Retrying SQL generation due to previous error: {}", state["error"])

    prompt = SCHEMA_CONTEXT + "\n\n" + GENERATE_SQL_PROMPT.format(
        question=state["question"],
        error_context=error_context,
    )

    try:
        resp = await _client().chat.completions.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        logger.error("[chat] Groq API error in generate_sql: {}", exc)
        raise

    sql = resp.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    logger.info("[chat] Generated SQL: {}", sql)
    return {"sql_query": sql, "error": None}


async def execute_sql_node(state: ChatState) -> dict:
    logger.info("[chat] execute_sql | query='{}'", state["sql_query"])
    try:
        rows = await execute_sql(state["sql_query"])
        logger.info("[chat] SQL returned {} row(s)", len(rows))
        return {"sql_result": rows, "error": None}
    except ValueError as exc:
        attempt = state.get("attempts", 0) + 1
        logger.warning("[chat] SQL execution failed (attempt {}): {}", attempt, exc)
        return {
            "sql_result": None,
            "error": str(exc),
            "attempts": attempt,
        }


def should_retry(state: ChatState) -> str:
    if state.get("error"):
        if state.get("attempts", 0) < 3:
            logger.info("[chat] Routing: retry (attempts={})", state.get("attempts"))
            return "retry"
        logger.warning("[chat] Routing: give_up after {} attempts", state.get("attempts"))
        return "give_up"
    logger.info("[chat] Routing: format")
    return "format"


async def format_answer_node(state: ChatState) -> dict:
    if state.get("error") and not state.get("sql_result"):
        logger.warning("[chat] format_answer: no result, returning fallback")
        return {"answer": "I was unable to answer that question. Please try rephrasing it."}

    logger.info("[chat] format_answer | {} row(s) to summarise", len(state.get("sql_result") or []))
    prompt = FORMAT_ANSWER_PROMPT.format(
        question=state["question"],
        results=str(state.get("sql_result", [])),
    )

    try:
        resp = await _client().chat.completions.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        logger.error("[chat] Groq API error in format_answer: {}", exc)
        raise

    answer = resp.choices[0].message.content.strip()
    logger.info("[chat] Final answer: {}", answer)
    return {"answer": answer}


def _build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("format_answer", format_answer_node)
    graph.set_entry_point("generate_sql")
    graph.add_edge("generate_sql", "execute_sql")
    graph.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "retry": "generate_sql",
            "give_up": "format_answer",
            "format": "format_answer",
        },
    )
    graph.add_edge("format_answer", END)
    return graph.compile()


_graph = _build_graph()


async def run_chat_agent(question: str) -> dict:
    logger.info("[chat] ── new request: '{}'", question)
    initial: ChatState = {
        "question": question,
        "sql_query": None,
        "sql_result": None,
        "answer": None,
        "attempts": 0,
        "error": None,
    }
    result = await _graph.ainvoke(initial)
    logger.info("[chat] ── done")
    return {
        "answer": result.get("answer") or "I was unable to answer that question.",
        "sql_query": result.get("sql_query"),
    }
