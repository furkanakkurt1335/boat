from datetime import datetime

from pydantic import BaseModel


class ValidationProfileCreate(BaseModel):
    treebank_id: int | None = None
    allowed_upos: list[str] | None = None
    allowed_deprels: list[str] | None = None
    allowed_features: dict[str, list[str]] | None = None
    allowed_misc: dict[str, list[str] | None] | None = None
    feature_order: list[str] | None = None
    custom_rules: list[dict] | None = None


class ValidationProfileUpdate(BaseModel):
    allowed_upos: list[str] | None = None
    allowed_deprels: list[str] | None = None
    allowed_features: dict[str, list[str]] | None = None
    allowed_misc: dict[str, list[str] | None] | None = None
    feature_order: list[str] | None = None
    custom_rules: list[dict] | None = None


class ValidationProfileRead(BaseModel):
    id: int
    treebank_id: int | None
    allowed_upos: list[str] | None
    allowed_deprels: list[str] | None
    allowed_features: dict[str, list[str]] | None
    allowed_misc: dict[str, list[str] | None] | None
    feature_order: list[str] | None
    custom_rules: list[dict] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ValidationError(BaseModel):
    word_id: str
    field: str
    value: str
    message: str
