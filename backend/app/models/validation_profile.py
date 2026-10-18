from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ValidationProfile(Base, TimestampMixin):
    __tablename__ = "validation_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    treebank_id: Mapped[int | None] = mapped_column(
        ForeignKey("treebanks.id", ondelete="CASCADE"), nullable=True, unique=True
    )
    allowed_upos: Mapped[list | None] = mapped_column(JSON, nullable=True)
    allowed_deprels: Mapped[list | None] = mapped_column(JSON, nullable=True)
    allowed_features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    allowed_misc: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feature_order: Mapped[list | None] = mapped_column(JSON, nullable=True)
    custom_rules: Mapped[list | None] = mapped_column(JSON, nullable=True)

    treebank: Mapped["Treebank | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        tb = self.treebank_id or "global"
        return f"<ValidationProfile for {tb}>"
