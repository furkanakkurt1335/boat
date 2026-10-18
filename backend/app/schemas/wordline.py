from pydantic import BaseModel


class WordLineCreate(BaseModel):
    id_f: str
    form: str
    lemma: str
    upos: str = "_"
    xpos: str = "_"
    feats: str = "_"
    head: str = "_"
    deprel: str = "_"
    deps: str = "_"
    misc: str = "_"


class WordLineRead(BaseModel):
    id: int
    annotation_id: int
    id_f: str
    form: str
    lemma: str
    upos: str
    xpos: str
    feats: str
    head: str
    deprel: str
    deps: str
    misc: str
    feats_parsed: dict[str, str] | None = None
    misc_parsed: dict[str, str] | None = None

    model_config = {"from_attributes": True}


class WordLineBatchUpdate(BaseModel):
    wordlines: list[WordLineCreate]
