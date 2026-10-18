from app.services.conllu import (
    export_conllu,
    parse_text,
    sort_wordlines_by_id,
    validate_uploaded_text,
)

SAMPLE_CONLLU = (
    "# sent_id = test-1\n"
    "# text = The cat sat.\n"
    "1\tThe\tthe\tDET\t_\t_\t2\tdet\t_\t_\n"
    "2\tcat\tcat\tNOUN\t_\t_\t3\tnsubj\t_\t_\n"
    "3\tsat\tsit\tVERB\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
    "4\t.\t.\tPUNCT\t_\t_\t3\tpunct\t_\t_\n"
    "\n"
)


def test_validate_valid():
    assert validate_uploaded_text(SAMPLE_CONLLU) is True


def test_validate_invalid():
    assert validate_uploaded_text("not a conllu file\n") is False


def test_validate_empty():
    assert validate_uploaded_text("") is True


def test_parse_single_sentence():
    sentences = parse_text(SAMPLE_CONLLU)
    assert len(sentences) == 1

    sent = sentences[0]
    assert sent["sent_id"] == "test-1"
    assert sent["text"] == "The cat sat."
    assert "1" in sent
    assert sent["1"]["form"] == "The"
    assert sent["1"]["upos"] == "DET"
    assert sent["3"]["deprel"] == "root"
    assert sent["4"]["misc"] == "_"


def test_parse_comments():
    text = (
        "# sent_id = s1\n"
        "# text = Hello\n"
        "# custom_key = custom_value\n"
        "1\tHello\thello\tINTJ\t_\t_\t0\troot\t_\t_\n"
        "\n"
    )
    sentences = parse_text(text)
    assert "metadata" in sentences[0]
    assert sentences[0]["metadata"]["custom_key"] == "custom_value"


def test_parse_multiword_token():
    text = (
        "# sent_id = mwt-1\n"
        "# text = Gidiyorum.\n"
        "1-2\tGidiyorum\t_\t_\t_\t_\t_\t_\t_\tSpaceAfter=No\n"
        "1\tGidi\tgitmek\tVERB\t_\t_\t0\troot\t_\t_\n"
        "2\tyorum\t_\tAUX\t_\t_\t1\taux\t_\t_\n"
        "3\t.\t.\tPUNCT\t_\t_\t1\tpunct\t_\t_\n"
        "\n"
    )
    sentences = parse_text(text)
    sent = sentences[0]
    assert "1-2" in sent
    assert "1" in sent
    assert "2" in sent


def test_sort_wordlines():
    wordlines = [
        {"id_f": "2", "form": "cat"},
        {"id_f": "1-2", "form": "thecat"},
        {"id_f": "1", "form": "the"},
        {"id_f": "3", "form": "sat"},
    ]
    sorted_wls = sort_wordlines_by_id(wordlines)
    assert [wl["id_f"] for wl in sorted_wls] == ["1-2", "1", "2", "3"]


def test_export_conllu():
    data = [
        {
            "sent_id": "test-1",
            "text": "The cat.",
            "metadata": {"source": "test"},
            "wordlines": [
                {
                    "id_f": "1",
                    "form": "The",
                    "lemma": "the",
                    "upos": "DET",
                    "xpos": "_",
                    "feats": "_",
                    "head": "2",
                    "deprel": "det",
                    "deps": "_",
                    "misc": "_",
                },
                {
                    "id_f": "2",
                    "form": "cat",
                    "lemma": "cat",
                    "upos": "NOUN",
                    "xpos": "_",
                    "feats": "_",
                    "head": "0",
                    "deprel": "root",
                    "deps": "_",
                    "misc": "SpaceAfter=No",
                },
            ],
        }
    ]
    result = export_conllu(data)
    assert "# sent_id = test-1" in result
    assert "# text = The cat." in result
    assert "# source = test" in result
    assert "1\tThe\tthe\tDET\t_\t_\t2\tdet\t_\t_" in result


def test_parse_multiple_sentences():
    text = SAMPLE_CONLLU + (
        "# sent_id = test-2\n"
        "# text = Dogs bark.\n"
        "1\tDogs\tdog\tNOUN\t_\t_\t2\tnsubj\t_\t_\n"
        "2\tbark\tbark\tVERB\t_\t_\t0\troot\t_\tSpaceAfter=No\n"
        "3\t.\t.\tPUNCT\t_\t_\t2\tpunct\t_\t_\n"
        "\n"
    )
    sentences = parse_text(text)
    assert len(sentences) == 2
    assert sentences[0]["sent_id"] == "test-1"
    assert sentences[1]["sent_id"] == "test-2"
