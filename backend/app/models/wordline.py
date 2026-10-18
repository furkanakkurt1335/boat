from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def _parse_ud_field(raw: str) -> dict[str, str] | None:
    """Parse a pipe-delimited UD field (FEATS/MISC) into a dict.

    '_' → None, 'Case=Nom|Number=Sing' → {'Case': 'Nom', 'Number': 'Sing'}
    """
    if raw == "_":
        return None
    result = {}
    for pair in raw.split("|"):
        if "=" in pair:
            key, _, value = pair.partition("=")
            result[key] = value
        else:
            # Bare values like 'SpaceAfter' without '=' — treat as flag
            result[pair] = ""
    return result


class WordLine(Base):
    __tablename__ = "wordlines"

    id: Mapped[int] = mapped_column(primary_key=True)
    annotation_id: Mapped[int] = mapped_column(
        ForeignKey("annotations.id", ondelete="CASCADE"), index=True
    )
    id_f: Mapped[str] = mapped_column(String(10))
    form: Mapped[str] = mapped_column(String(200))
    lemma: Mapped[str] = mapped_column(String(200))
    upos: Mapped[str] = mapped_column(String(20))
    xpos: Mapped[str] = mapped_column(String(100))
    feats: Mapped[str] = mapped_column(String(1000))
    head: Mapped[str] = mapped_column(String(10))
    deprel: Mapped[str] = mapped_column(String(100))
    deps: Mapped[str] = mapped_column(String(200))
    misc: Mapped[str] = mapped_column(String(500))

    # Structured versions for querying (auto-populated from raw strings)
    feats_parsed: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    misc_parsed: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    annotation: Mapped["Annotation"] = relationship(back_populates="wordlines")  # noqa: F821

    def populate_parsed_fields(self) -> None:
        """Parse feats and misc strings into their JSON counterparts."""
        self.feats_parsed = _parse_ud_field(self.feats)
        self.misc_parsed = _parse_ud_field(self.misc)

    def __repr__(self) -> str:
        return f"<WordLine {self.id_f} {self.form}>"
