from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    job_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    company: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC),
        nullable=False,
    )