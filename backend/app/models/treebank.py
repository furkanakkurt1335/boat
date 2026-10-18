from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Treebank(Base, TimestampMixin):
    __tablename__ = "treebanks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(30))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    sentences: Mapped[list["Sentence"]] = relationship(  # noqa: F821
        back_populates="treebank", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Treebank {self.title}>"
