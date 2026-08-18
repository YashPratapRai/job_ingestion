from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class JobSchema(BaseModel):
    external_id: str = Field(min_length=1)
    title: str = Field(min_length=1)

    company: str | None = None
    location: str | None = None

    description: str = ""

    url: HttpUrl

    published_at: datetime | None = None

    source: str = Field(min_length=1)