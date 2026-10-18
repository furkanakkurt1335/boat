from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.annotation import AnnotationStatus
from app.schemas.wordline import WordLineRead


class AnnotationCreate(BaseModel):
    sentence_id: int
    notes: str = ""
    status: int = 0
    is_template: bool = False

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        valid = {s.value for s in AnnotationStatus}
        if v not in valid:
            raise ValueError(f"status must be one of {sorted(valid)}")
        return v


class AnnotationUpdate(BaseModel):
    notes: str | None = None
    status: int | None = None
    is_gold: bool | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int | None) -> int | None:
        if v is not None:
            valid = {s.value for s in AnnotationStatus}
            if v not in valid:
                raise ValueError(f"status must be one of {sorted(valid)}")
        return v


class AnnotationRead(BaseModel):
    id: int
    annotator_id: int
    sentence_id: int
    notes: str
    status: int
    status_label: str = ""
    is_template: bool
    is_gold: bool
    created_at: datetime
    annotator_username: str | None = None

    model_config = {"from_attributes": True}

    def model_post_init(self, __context: object) -> None:
        if not self.status_label:
            try:
                self.status_label = AnnotationStatus(self.status).name
            except ValueError:
                self.status_label = "UNKNOWN"


class AnnotationDetail(AnnotationRead):
    wordlines: list[WordLineRead] = []
    annotator_username: str | None = None
    sentence_sent_id: str | None = None
    sentence_text: str | None = None
    sentence_metadata: dict | None = None
    treebank_title: str | None = None
    treebank_id: int | None = None
    treebank_created_by: int | None = None
    sentence_order: int | None = None
