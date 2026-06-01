from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

from backend.agent.chat_agent import run_chat_agent

router = APIRouter()


class ChatRequest(BaseModel):
    question: str
    show_sql: bool = False


class ChatResponse(BaseModel):
    answer: str
    sql_used: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    logger.info("[chat] POST /chat question='{}'", body.question)
    try:
        result = await run_chat_agent(body.question)
        return ChatResponse(
            answer=result["answer"],
            sql_used=result["sql_query"] if body.show_sql else None,
        )
    except Exception as exc:
        logger.exception("[chat] Unhandled error: {}", exc)
        return ChatResponse(answer="The assistant is currently unavailable. Please try again later.")
