"""Standalone entry point for the MyNeta integrity scrape.

Runs the pipeline in its own process (not the API server), so it survives
backend restarts and can't block the web event loop. Honours LLM_PROVIDER
from .env (e.g. ollama). Usage from project root:

    .venv311\\Scripts\\python.exe -m backend.run_scrape            # use cached HTML
    .venv311\\Scripts\\python.exe -m backend.run_scrape --force    # re-download pages
"""
import asyncio
import sys

from backend.agents.myneta_pipeline import run

if __name__ == "__main__":
    force = "--force" in sys.argv
    run_id = asyncio.run(run(force_refresh=force))
    print(f"run_id {run_id}")
