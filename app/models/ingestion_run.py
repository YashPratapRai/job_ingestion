from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    records_fetched: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    records_inserted: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    records_skipped: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )