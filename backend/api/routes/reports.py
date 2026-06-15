"""Discrepancy reports — user-submitted corrections for MP data."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import MPProfile, MpDiscrepancyReport
from backend.db.session import get_session

router = APIRouter(prefix="/reports", tags=["reports"])

VALID_TYPES = {
    "performance": "Attendance / Questions / Debates / PMBs",
    "criminal_cases": "Criminal cases",
    "assets": "Asset declarations",
    "mplads": "Constituency funds (MPLADS)",
    "statements": "Statements / Quotes",
    "profile": "Profile information",
    "other": "Other",
}


class ReportIn(BaseModel):
    discrepancy_type: str
    description: str
    contact_email: str | None = None

    @field_validator("discrepancy_type")
    @classmethod
    def _valid_type(cls, v: str) -> str:
        if v not in VALID_TYPES:
            raise ValueError(f"discrepancy_type must be one of: {', '.join(VALID_TYPES)}")
        return v

    @field_validator("description")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("description must be at least 10 characters")
        if len(v) > 2000:
            raise ValueError("description must be under 2000 characters")
        return v


class ReportOut(BaseModel):
    id: int
    mp_slug: str
    mp_name: str | None
    discrepancy_type: str
    discrepancy_label: str
    description: str
    contact_email: str | None
    status: str
    admin_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/{slug}", response_model=dict)
async def submit_report(
    slug: str,
    body: ReportIn,
    session: AsyncSession = Depends(get_session),
):
    mp = (await session.execute(
        select(MPProfile).where(MPProfile.prs_slug == slug)
    )).scalar_one_or_none()

    if mp is None:
        raise HTTPException(status_code=404, detail="MP not found")

    report = MpDiscrepancyReport(
        mp_slug=slug,
        mp_id=mp.id,
        discrepancy_type=body.discrepancy_type,
        description=body.description,
        contact_email=body.contact_email or None,
        status="new",
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return {"id": report.id, "status": "received"}


@router.get("", response_model=list[ReportOut])
async def list_reports(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """Admin view — list all discrepancy reports, newest first."""
    q = select(MpDiscrepancyReport, MPProfile.name).outerjoin(
        MPProfile, MPProfile.id == MpDiscrepancyReport.mp_id
    ).order_by(desc(MpDiscrepancyReport.created_at))

    if status:
        q = q.where(MpDiscrepancyReport.status == status)

    rows = (await session.execute(q)).all()

    return [
        ReportOut(
            id=r.id,
            mp_slug=r.mp_slug,
            mp_name=name,
            discrepancy_type=r.discrepancy_type,
            discrepancy_label=VALID_TYPES.get(r.discrepancy_type, r.discrepancy_type),
            description=r.description,
            contact_email=r.contact_email,
            status=r.status,
            admin_notes=r.admin_notes,
            created_at=r.created_at,
        )
        for r, name in rows
    ]
