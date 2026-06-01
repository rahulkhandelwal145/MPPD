import re

from sqlalchemy import text

from backend.db.session import AsyncSessionLocal


async def execute_sql(query: str) -> list[dict]:
    """
    Runs a SELECT query against MySQL.
    Hard-blocks any non-SELECT query regardless of what the LLM generated.
    """
    cleaned = query.strip().upper()

    if not cleaned.startswith("SELECT"):
        raise ValueError("Only SELECT queries are permitted.")

    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "EXEC"]
    for word in forbidden:
        if re.search(r"\b" + word + r"\b", cleaned):
            raise ValueError(f"Forbidden keyword in query: {word}")

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text(query))
            rows = result.fetchmany(20)
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            raise ValueError(f"Query execution failed: {str(e)}")
