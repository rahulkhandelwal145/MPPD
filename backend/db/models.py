from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MPProfile(Base):
    __tablename__ = "mp_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    prs_slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    constituency: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    party: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_minister: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_speaker: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_loa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    education: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lok_sabha_term: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("18"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"), onupdate=datetime.utcnow)

    raw_data: Mapped[list["MPRawData"]] = relationship("MPRawData", back_populates="mp_profile")
    scores: Mapped[list["MPScore"]] = relationship("MPScore", back_populates="mp_profile")


class MPRawData(Base):
    __tablename__ = "mp_raw_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mp_id: Mapped[int] = mapped_column(ForeignKey("mp_profiles.id"), nullable=False)
    attendance_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    questions_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    debates_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pmb_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mplads_utilization: Mapped[float | None] = mapped_column(Float, nullable=True)
    national_avg_attendance: Mapped[float | None] = mapped_column(Float, nullable=True)
    state_avg_attendance: Mapped[float | None] = mapped_column(Float, nullable=True)
    national_avg_questions: Mapped[float | None] = mapped_column(Float, nullable=True)
    state_avg_questions: Mapped[float | None] = mapped_column(Float, nullable=True)
    national_avg_debates: Mapped[float | None] = mapped_column(Float, nullable=True)
    state_avg_debates: Mapped[float | None] = mapped_column(Float, nullable=True)
    national_avg_pmb: Mapped[float | None] = mapped_column(Float, nullable=True)
    state_avg_pmb: Mapped[float | None] = mapped_column(Float, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))

    mp_profile: Mapped[MPProfile] = relationship("MPProfile", back_populates="raw_data")


class MPScore(Base):
    __tablename__ = "mp_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mp_id: Mapped[int] = mapped_column(ForeignKey("mp_profiles.id"), nullable=False)
    peer_group: Mapped[str] = mapped_column(String(20), nullable=False)
    attendance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    questions_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    debates_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pmb_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    attendance_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    questions_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    debates_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pmb_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_peers: Mapped[int] = mapped_column(Integer, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))

    mp_profile: Mapped[MPProfile] = relationship("MPProfile", back_populates="scores")


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    mps_scraped: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mps_scored: Mapped[int | None] = mapped_column(Integer, nullable=True)
    errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
