from datetime import datetime

from pydantic import BaseModel, Field


class TreebankCreate(BaseModel):
    title: str = Field(min_length=1, max_length=30)
    language: str = Field(min_length=1, max_length=30)


class TreebankRead(BaseModel):
    id: int
    title: str
    language: str
    created_by: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TreebankWithProgress(TreebankRead):
    sentence_count: int = 0
    annotation_count: int = 0
    complete_count: int = 0
