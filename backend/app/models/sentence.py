from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Sentence(Base, TimestampMixin):
    __tablename__ = "sentences"
    __table_args__ = (UniqueConstraint("sent_id", "text", "treebank_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order: Mapped[int] = mapped_column()
    treebank_id: Mapped[int] = mapped_column(
        ForeignKey("treebanks.id", ondelete="CASCADE"),
        index=True,
    )
    sent_id: Mapped[str] = mapped_column(String(30), index=True)
    text: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    treebank: Mapped["Treebank"] = relationship(back_populates="sentences")  # noqa: F821
    annotations: Mapped[list["Annotation"]] = relationship(  # noqa: F821
        back_populates="sentence", cascade="all, delete-orphan"
    )
    discussion: Mapped[list["Comment"]] = relationship(  # noqa: F821
        back_populates="sentence", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Sentence {self.sent_id}>"
