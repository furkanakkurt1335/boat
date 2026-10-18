from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    text: str = Field(min_length=1)


class CommentRead(BaseModel):
    id: int
    sentence_id: int
    user_id: int
    username: str
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
