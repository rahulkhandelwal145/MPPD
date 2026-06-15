from datetime import datetime
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, text
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
    terms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
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


class MpAffidavit(Base):
    __tablename__ = "mp_affidavits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mp_id: Mapped[int | None] = mapped_column(ForeignKey("mp_profiles.id"), nullable=True)
    myneta_candidate_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    candidate_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    constituency: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    party: Mapped[str | None] = mapped_column(String(100), nullable=True)
    match_confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)
    best_match_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    best_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    total_criminal_cases: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    total_convictions: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    convictions_serious: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    has_serious_cases: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    has_conviction: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    total_assets: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    movable_assets: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    immovable_assets: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_liabilities: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    self_income: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    spouse_income: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    education: Mapped[str | None] = mapped_column(String(300), nullable=True)
    extraction_success: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))

    criminal_cases: Mapped[list["MpCriminalCase"]] = relationship("MpCriminalCase", back_populates="affidavit")
    asset_history: Mapped[list["MpAssetHistory"]] = relationship("MpAssetHistory", back_populates="affidavit")


class MpMplads(Base):
    __tablename__ = "mp_mplads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # NULL when the CSV name could not be confidently matched to a profile.
    mp_id: Mapped[int | None] = mapped_column(ForeignKey("mp_profiles.id"), nullable=True)
    # Name exactly as in the CSV — also the upsert key, so re-ingesting the same
    # CSV updates rows in place instead of duplicating them.
    mp_name_raw: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    constituency: Mapped[str | None] = mapped_column(String(200), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    match_confidence: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Raw values from the CSV
    allocated_amount: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    total_expenditure: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    utilization_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_works: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_works: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_rate_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    transaction_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    successful_payments: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pending_payments: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Computed percentile-rank scores (0–100); NULL where the metric is undefined.
    utilization_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mplads_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))


class MpCriminalCase(Base):
    __tablename__ = "mp_criminal_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    affidavit_id: Mapped[int] = mapped_column(ForeignKey("mp_affidavits.id"), nullable=False)
    ipc_section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_serious: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    is_conviction: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))

    affidavit: Mapped["MpAffidavit"] = relationship("MpAffidavit", back_populates="criminal_cases")


class MpAssetHistory(Base):
    __tablename__ = "mp_asset_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    affidavit_id: Mapped[int] = mapped_column(ForeignKey("mp_affidavits.id"), nullable=False)
    election_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    declared_assets: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    affidavit: Mapped["MpAffidavit"] = relationship("MpAffidavit", back_populates="asset_history")


# ─── Phase 4 — Public Statement Monitor ────────────────────────────────────────
# Not managed by Alembic; created on startup via Base.metadata.create_all().

class MpNewsArticle(Base):
    __tablename__ = "mp_news_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mp_id: Mapped[int] = mapped_column(ForeignKey("mp_profiles.id"), nullable=False)
    # Resolved publisher URL — also the upsert/dedupe key so an article isn't
    # re-fetched or re-classified across weekly runs.
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    article_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    quotes_extracted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))

    statements: Mapped[list["MpStatement"]] = relationship("MpStatement", back_populates="article")


class MpStatement(Base):
    __tablename__ = "mp_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mp_id: Mapped[int] = mapped_column(ForeignKey("mp_profiles.id"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("mp_news_articles.id"), nullable=False)

    # The statement itself — always the exact verbatim quote, never paraphrased.
    verbatim: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification. Only A/B/C/D rows are ever stored; E is discarded.
    category: Mapped[str | None] = mapped_column(String(5), nullable=True)
    category_group: Mapped[str | None] = mapped_column(String(1), nullable=True)
    constitutional_anchor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    data_contradicted: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    article_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    classified_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))

    article: Mapped["MpNewsArticle"] = relationship("MpNewsArticle", back_populates="statements")


# ─── Discrepancy Reports ────────────────────────────────────────────────────
# Not managed by Alembic; created on startup via Base.metadata.create_all().

class MpDiscrepancyReport(Base):
    __tablename__ = "mp_discrepancy_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mp_slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    mp_id: Mapped[int | None] = mapped_column(ForeignKey("mp_profiles.id"), nullable=True)
    discrepancy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'new'"))
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=text("NOW()"))
