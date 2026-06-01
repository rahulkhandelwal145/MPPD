from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas import PipelineRunRequest, PipelineStatusResponse
from backend.agents.orchestrator import run_pipeline
from backend.db.models import PipelineRun
from backend.db.session import get_session

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run", response_model=dict)
async def trigger_pipeline(
    payload: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    run = PipelineRun(status="running", mps_scraped=0, mps_scored=0, errors=[])
    session.add(run)
    await session.commit()
    await session.refresh(run)

    background_tasks.add_task(run_pipeline, run.id, payload.force_refresh)
    return {"run_id": run.id}


@router.get("/status/{run_id}", response_model=PipelineStatusResponse)
async def pipeline_status(run_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.get(PipelineRun, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return PipelineStatusResponse(
        run_id=result.id,
        status=result.status,
        mps_scraped=result.mps_scraped,
        mps_scored=result.mps_scored,
        errors=result.errors,
        started_at=result.started_at,
        completed_at=result.completed_at,
    )
