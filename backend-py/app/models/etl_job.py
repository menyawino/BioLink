"""SQLAlchemy model for persistent ETL job tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class ETLJobModel(Base):
    """Persistent ETL job state — survives backend restarts."""

    __tablename__ = "etl_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), nullable=False, default="pending")
    # pending | running | completed | failed | cancelled

    table_name = Column(String(128), nullable=True)
    schema_name = Column(String(128), nullable=True, default="public")
    datasets = Column(JSONB, nullable=True)
    dataset_name = Column(String(128), nullable=True)
    skip_superset = Column(String(8), nullable=True, default="false")

    lineage = Column(JSONB, nullable=True, default=list)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ETLJob(job_id='{self.job_id}', status='{self.status}')>"
