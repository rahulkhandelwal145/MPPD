from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MPSummary(BaseModel):
    name: str
    prs_slug: str
    constituency: str | None
    state: str | None
    party: str | None
    is_minister: bool
    is_speaker: bool
    is_loa: bool
    age: int | None
    gender: str | None
    education: str | None
    terms: int | None
    image_url: str | None
    attendance_score: float | None
    questions_score: float | None
    debates_score: float | None
    pmb_score: float | None
    peer_group: str
    total_peers: int
    # Integrity summary (null when the MP has no scraped affidavit)
    criminal_cases: int | None = None
    convictions: int | None = None
    convictions_serious: int | None = None
    total_assets: int | None = None
    has_serious_cases: bool | None = None
    # % change in declared assets since the MP's most recent prior election,
    # and since their earliest declaration on record (null for first-time MPs).
    asset_growth_pct: float | None = None
    asset_growth_since: str | None = None
    asset_growth_first_pct: float | None = None
    asset_growth_first_since: str | None = None
    # Chronological [{year, assets}] for the asset-trajectory sparkline.
    asset_series: list[dict] | None = None
    # Absolute 0–100 integrity score derived from convictions (see core.scoring)
    clean_record_score: int | None = None
    # Mean of the MP's available 0–100 metrics (incl. clean_record_score)
    total_score: float | None = None
    # MPLADS local-area-development summary (null when the MP has no matched row).
    # Kept separate from total_score — it measures fund use, not parliamentary work.
    mplads_score: int | None = None
    mplads_utilization_pct: float | None = None


class MPRawData(BaseModel):
    attendance_pct: float | None
    questions_count: int | None
    debates_count: int | None
    pmb_count: int | None
    mplads_utilization: float | None
    national_avg_attendance: float | None
    state_avg_attendance: float | None
    national_avg_questions: float | None
    state_avg_questions: float | None
    national_avg_debates: float | None
    state_avg_debates: float | None
    national_avg_pmb: float | None
    state_avg_pmb: float | None


class MpladsData(BaseModel):
    """Phase 3 MPLADS local-area-development funds (null when the MP has no
    matched MPLADS row). Allocations include 17th-LS carry-forward; scores are
    peer-relative percentile ranks so the carry-forward doesn't skew fairness."""
    match_confidence: str | None
    allocated_amount: int | None
    total_expenditure: int | None
    utilization_pct: float | None
    completed_works: int | None
    recommended_works: int | None
    completion_rate_pct: float | None
    transaction_count: int | None
    successful_payments: int | None
    pending_payments: int | None
    utilization_score: int | None
    completion_score: int | None
    payment_score: int | None
    mplads_score: int | None


class MPDetail(BaseModel):
    name: str
    prs_slug: str
    constituency: str | None
    state: str | None
    party: str | None
    is_minister: bool
    is_speaker: bool
    is_loa: bool
    age: int | None
    gender: str | None
    education: str | None
    terms: int | None
    image_url: str | None
    raw: MPRawData
    scores: dict[str, float | None]
    ranks: dict[str, int | None]
    peer_group: str
    scored_at: datetime | None
    mplads: MpladsData | None = None


class LeaderboardResponse(BaseModel):
    results: list[MPSummary]


class StatsSummary(BaseModel):
    total_mps: int
    total_ministers: int
    last_run_at: datetime | None
    last_run_status: str | None
    avg_attendance_score: float | None
    avg_questions_score: float | None
    avg_debates_score: float | None
    avg_pmb_score: float | None


class PipelineRunRequest(BaseModel):
    force_refresh: bool = False


class PipelineStatusResponse(BaseModel):
    run_id: int
    status: str
    mps_scraped: int | None
    mps_scored: int | None
    errors: list[dict[str, Any]] | None
    started_at: datetime
    completed_at: datetime | None
