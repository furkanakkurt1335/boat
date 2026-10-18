"""Round-trip fidelity tests using real AMGIC treebank data."""

from pathlib import Path

from app.services.conllu import export_conllu, parse_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_roundtrip_amgic():
    """Parse AMGIC CoNLL-U, export it, re-parse — verify no data loss."""
    original = (FIXTURES / "amgic_sample.conllu").read_text(encoding="utf-8")

    sentences = parse_text(original)
    assert len(sentences) == 3

    # Verify sentence 1 metadata
    s1 = sentences[0]
    assert s1["sent_id"] == "1"
    assert "dialect" in s1["metadata"]
    assert s1["metadata"]["dialect"] == "Silliot"
    assert "text[ell]" in s1["metadata"]
    assert "text[eng]" in s1["metadata"]
    assert s1["metadata"]["source"] == "Kostakis 1968:116"

    # Verify sentence 2 has empty text[eng]
    s2 = sentences[1]
    assert s2["metadata"]["text[eng]"] == ""

    # Verify language contact markers in MISC are preserved
    # Token 17 in sentence 1: LC=Yes|MorphSynC=FrGrM|...
    assert "17" in s1
    assert "LC=Yes" in s1["17"]["misc"]
    assert "OrigLang=tr" in s1["17"]["misc"]

    # Export to CoNLL-U
    export_data = []
    for sent in sentences:
        wordlines = []
        for key, val in sent.items():
            if key in ("sent_id", "text", "metadata"):
                continue
            wordlines.append({"id_f": key, **val})
        export_data.append(
            {
                "sent_id": sent["sent_id"],
                "text": sent["text"],
                "metadata": sent.get("metadata"),
                "wordlines": wordlines,
            }
        )

    exported = export_conllu(export_data)

    # Re-parse the exported text
    reparsed = parse_text(exported)
    assert len(reparsed) == 3

    # Verify round-trip: same number of tokens per sentence
    for orig, reparse in zip(sentences, reparsed, strict=True):
        orig_tokens = {k for k in orig if k not in ("sent_id", "text", "metadata")}
        reparse_tokens = {k for k in reparse if k not in ("sent_id", "text", "metadata")}
        assert orig_tokens == reparse_tokens, f"Token mismatch in {orig['sent_id']}"

    # Verify round-trip: comments preserved
    for orig, reparse in zip(sentences, reparsed, strict=True):
        assert orig.get("metadata", {}) == reparse.get("metadata", {}), (
            f"Comment mismatch in {orig['sent_id']}"
        )

    # Verify round-trip: field values preserved
    for orig, reparse in zip(sentences, reparsed, strict=True):
        for tok_id in orig:
            if tok_id in ("sent_id", "text", "metadata"):
                continue
            for field in (
                "form",
                "lemma",
                "upos",
                "xpos",
                "feats",
                "head",
                "deprel",
                "deps",
                "misc",
            ):
                assert orig[tok_id][field] == reparse[tok_id][field], (
                    f"Field {field} mismatch for token {tok_id} in sentence {orig['sent_id']}"
                )


def test_structured_misc_parsing():
    """Verify that MISC fields with LC/contact metadata parse correctly."""
    from app.models.wordline import _parse_ud_field

    # Token 17 from AMGIC sentence 1
    misc = "LC=Yes|MorphSynC=FrGrM|MorphSynSC=QPart|Orig=mI|OrigLang=tr"
    parsed = _parse_ud_field(misc)
    assert parsed == {
        "LC": "Yes",
        "MorphSynC": "FrGrM",
        "MorphSynSC": "QPart",
        "Orig": "mI",
        "OrigLang": "tr",
    }

    # SpaceAfter=No
    assert _parse_ud_field("SpaceAfter=No") == {"SpaceAfter": "No"}

    # Underscore = None
    assert _parse_ud_field("_") is None


def test_structured_feats_parsing():
    """Verify morphological features parse correctly."""
    from app.models.wordline import _parse_ud_field

    feats = "Case=Nom|Definite=Ind|Gender=Neut|Number=Sing|PronType=Art"
    parsed = _parse_ud_field(feats)
    assert parsed == {
        "Case": "Nom",
        "Definite": "Ind",
        "Gender": "Neut",
        "Number": "Sing",
        "PronType": "Art",
    }
