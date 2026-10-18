from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Guideline(Base, TimestampMixin):
    __tablename__ = "guidelines"

    id: Mapped[int] = mapped_column(primary_key=True)
    treebank_id: Mapped[int] = mapped_column(
        ForeignKey("treebanks.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(100), index=True)
    text: Mapped[str] = mapped_column(Text)

    treebank: Mapped["Treebank"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Guideline {self.key}>"
