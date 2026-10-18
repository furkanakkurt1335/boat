"""WordLine copy utilities."""

from app.models.wordline import WordLine

# Fields copied from a source WordLine (excludes id, annotation_id, and parsed JSON fields).
_COPY_FIELDS = ("id_f", "form", "lemma", "upos", "xpos", "feats", "head", "deprel", "deps", "misc")


def copy_wordlines(source_wordlines: list[WordLine], target_annotation_id: int) -> list[WordLine]:
    """Create WordLine copies from *source_wordlines* for a new annotation.

    Each new WordLine gets its parsed JSON fields populated automatically.
    The caller is responsible for adding the returned objects to the session.
    """
    new_wordlines = []
    for wl in source_wordlines:
        new_wl = WordLine(
            annotation_id=target_annotation_id,
            **{f: getattr(wl, f) for f in _COPY_FIELDS},
        )
        new_wl.populate_parsed_fields()
        new_wordlines.append(new_wl)
    return new_wordlines
