import asyncio
from loguru import logger

from backend.agents.mplads_agent import run_mplads_agent
from backend.agents.prs_scraper_agent import run_prs_scraper
from backend.agents.scoring_agent import run_scoring_agent
from backend.agents.store_agent import store_pipeline_results


async def run_pipeline(run_id: int, force_refresh: bool = False) -> None:
    state = {"errors": []}
    try:
        scraper_result = await run_prs_scraper(run_id, force_refresh)
        state.update(scraper_result)
        state["mp_slugs"] = scraper_result.get("mp_slugs", [])

        mplads_result = await run_mplads_agent(run_id, state.get("raw_mp_data", []))
        state.update(mplads_result)

        scored_result = await run_scoring_agent(state)
        state.update(scored_result)

        await store_pipeline_results(state, run_id)
    except Exception as exc:
        logger.exception("Pipeline failed for run %s", run_id)
        state.setdefault("errors", []).append({"slug": "pipeline", "reason": str(exc)})
        try:
            await store_pipeline_results(state, run_id)
        except Exception:
            logger.exception("Failed to update pipeline run after fatal error %s", run_id)
