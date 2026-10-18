from datetime import datetime

from pydantic import BaseModel


class GuidelineCreate(BaseModel):
    key: str
    text: str


class GuidelineUpdate(BaseModel):
    text: str


class GuidelineRead(BaseModel):
    id: int
    treebank_id: int
    key: str
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}
