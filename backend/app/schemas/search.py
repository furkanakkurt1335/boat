from pydantic import BaseModel, Field

from app.schemas.wordline import WordLineRead


class SearchQuery(BaseModel):
    form: str | None = None
    lemma: str | None = None
    upos: str | None = None
    xpos: str | None = None
    feats: str | None = None
    head: str | None = None
    deprel: str | None = None
    deps: str | None = None
    misc: str | None = None
    sent_id: str | None = None
    text: str | None = None
    treebank_title: str | None = None


class SearchResult(WordLineRead):
    sentence_sent_id: str
    sentence_text: str
    treebank_title: str
    annotator_username: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int


# --- Structural search schemas ---


class NodeConstraint(BaseModel):
    """Constraints on a single token's properties."""

    upos: list[str] | None = None
    feats: dict[str, list[str]] | None = None
    form: str | None = None
    lemma: str | None = None


class RelationConstraint(NodeConstraint):
    """Constraints on a token reached via a dependency relation."""

    deprel: list[str] | None = None


class StructuralQuery(BaseModel):
    """Query for structural (tree-pattern) search over UD annotations."""

    target: NodeConstraint
    head_constraint: RelationConstraint | None = None
    dependent_constraints: list[RelationConstraint] | None = None
    negated_dependents: list[RelationConstraint] | None = None
    treebank_id: int | None = None
    limit: int = Field(50, le=200, ge=1)
    offset: int = Field(0, ge=0)


class StructuralMatch(BaseModel):
    """A single sentence result from a structural search."""

    sentence_id: int
    sent_id: str
    text: str
    treebank_id: int
    treebank_title: str
    matched_token_ids: list[str]


class StructuralSearchResponse(BaseModel):
    """Paginated response for structural search."""

    results: list[StructuralMatch]
    total: int


# --- Pattern-based structural search (udsearch syntax) ---


class PatternQuery(BaseModel):
    """Query using udsearch pattern syntax (single-node or structural)."""

    pattern: str = Field(
        ...,
        description='Pattern string, e.g. "UPOS=NOUN & Case=Dat" or '
        '"v: [UPOS=VERB]\\ns: [] -nsubj-> v"',
    )
    treebank_id: int | None = None
    limit: int = Field(50, le=200, ge=1)
    offset: int = Field(0, ge=0)


# --- Batch rewrite schemas ---


class RewriteRequest(BaseModel):
    """Request for batch rewriting tokens that match a pattern."""

    pattern: str = Field(
        ...,
        description='Pattern string, e.g. "UPOS=NOUN & Case=Dat" or structural pattern',
    )
    operations: list[str] = Field(
        ...,
        description='Rewrite operations, e.g. ["UPOS=ADJ", "-Case", "s.Case=Nom"]',
    )
    treebank_id: int | None = None
    annotation_scope: str = Field(
        "template",
        description="Which annotations to rewrite: 'template', 'mine', or 'all'",
    )


class RewriteChange(BaseModel):
    """A single token change from a rewrite operation."""

    sentence_id: int
    sent_id: str
    token_id: str
    form: str
    node_name: str
    descriptions: list[str]


class RewritePreviewResponse(BaseModel):
    """Preview of batch rewrite changes (not yet applied)."""

    changes: list[RewriteChange]
    total_tokens: int
    total_sentences: int


class RewriteApplyResponse(BaseModel):
    """Result of applying batch rewrite operations."""

    applied: int
    skipped: int
    changes: list[RewriteChange]
