"""CoNLL-U file parsing, validation, and export utilities."""

import json
import re
from pathlib import Path

FIELDS = ("form", "lemma", "upos", "xpos", "feats", "head", "deprel", "deps", "misc")

_data_dir = Path(__file__).resolve().parent.parent / "data"

with (_data_dir / "language_ids.json").open(encoding="utf-8") as _f:
    LANGUAGES: dict[str, str] = json.load(_f)

# Regex: a sentence is one or more comment lines (starting with #) followed by
# one or more word lines (10 tab-separated fields).
_SENTENCE_RE = re.compile(r"(?:#[^\n]*\n)+(?:(?:[^\t\n]+\t){9}[^\t\n]+\n)+")
_COMMENT_RE = re.compile(r"#(.+)=(.*)")
_WORD_RE = re.compile(r"(?:.+\t){9}.+")


def validate_uploaded_text(text: str) -> bool:
    """Return True if *text* is valid CoNLL-U (all content consumed by sentence pattern)."""
    remaining = _SENTENCE_RE.sub("", text)
    return remaining.strip() == ""


def parse_text(text: str) -> list[dict]:
    """Parse CoNLL-U text into a list of sentence dicts.

    Each sentence dict has keys:
        sent_id, text, metadata (optional dict),
        and word-id keys ("1", "2", "1-2", …) mapping to field dicts.
    """
    raw_sentences = _SENTENCE_RE.findall(text)
    sentences: list[dict] = []

    for raw in raw_sentences:
        sentence: dict = {}
        for line in raw.split("\n"):
            if line.startswith("#"):
                m = _COMMENT_RE.match(line)
                if m and len(m.groups()) == 2:
                    key, value = m.group(1).strip(), m.group(2).strip()
                    if key in ("sent_id", "text"):
                        sentence[key] = value
                    else:
                        sentence.setdefault("metadata", {})[key] = value
            else:
                m = _WORD_RE.match(line)
                if m:
                    cols = m.group().strip().split("\t")
                    id_f = cols[0]
                    sentence[id_f] = {FIELDS[i]: cols[i + 1] for i in range(9)}
        sentences.append(sentence)

    return sentences


def sort_wordlines_by_id(wordlines: list[dict]) -> list[dict]:
    """Sort a list of wordline dicts by CoNLL-U ID order (handling multiword tokens)."""
    result: list[dict] = []
    id_map = {wl["id_f"]: wl for wl in wordlines}
    max_id = len(wordlines) * 5  # generous upper bound

    for i in range(1, max_id + 1):
        mwt_key = f"{i}-{i + 1}"
        if mwt_key in id_map:
            result.append(id_map[mwt_key])
        single_key = str(i)
        if single_key in id_map:
            result.append(id_map[single_key])

    return result


def _format_sentence_block(sent: dict) -> str:
    """Format a single sentence dict as a CoNLL-U block (with trailing blank line)."""
    lines: list[str] = []
    lines.append(f"# sent_id = {sent['sent_id']}")
    lines.append(f"# text = {sent['text']}")
    if sent.get("metadata"):
        for key, value in sent["metadata"].items():
            lines.append(f"# {key} = {value}")

    sorted_wls = sort_wordlines_by_id(sent["wordlines"])
    for wl in sorted_wls:
        fields = "\t".join(wl[f] for f in ("id_f", *FIELDS))
        lines.append(fields)
    lines.append("")  # blank line between sentences
    return "\n".join(lines) + "\n"


def export_conllu(sentences: list[dict]) -> str:
    """Export a list of sentence dicts (with nested wordlines) to CoNLL-U text.

    Expected structure per sentence:
        {
            "sent_id": str,
            "text": str,
            "metadata": {key: value, ...} | None,
            "wordlines": [{"id_f": ..., "form": ..., ...}, ...]
        }
    """
    if not sentences:
        return ""
    return "".join(_format_sentence_block(sent) for sent in sentences)
