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
    age: int | None
    gender: str | None
    education: str | None
    attendance_score: float | None
    questions_score: float | None
    debates_score: float | None
    pmb_score: float | None
    peer_group: str
    total_peers: int


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


class MPDetail(BaseModel):
    name: str
    prs_slug: str
    constituency: str | None
    state: str | None
    party: str | None
    is_minister: bool
    is_speaker: bool
    age: int | None
    gender: str | None
    education: str | None
    raw: MPRawData
    scores: dict[str, float | None]
    ranks: dict[str, int | None]
    peer_group: str
    scored_at: datetime | None


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
