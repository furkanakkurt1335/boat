import enum

from sqlalchemy import Boolean, ForeignKey, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AnnotationStatus(enum.IntEnum):
    NEW = 0
    DRAFT = 1
    SUBMITTED = 2
    APPROVED = 3
    REJECTED = 4


class Annotation(Base, TimestampMixin):
    __tablename__ = "annotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    annotator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    sentence_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"),
        index=True,
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=AnnotationStatus.NEW)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)
    is_gold: Mapped[bool] = mapped_column(Boolean, default=False)

    annotator: Mapped["User"] = relationship(back_populates="annotations")  # noqa: F821
    sentence: Mapped["Sentence"] = relationship(back_populates="annotations")  # noqa: F821
    wordlines: Mapped[list["WordLine"]] = relationship(  # noqa: F821
        back_populates="annotation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Annotation {self.id} by user {self.annotator_id}>"
