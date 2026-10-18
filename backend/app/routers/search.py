from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.annotation import Annotation, AnnotationStatus
from app.models.sentence import Sentence
from app.models.treebank import Treebank
from app.models.user import User
from app.models.wordline import WordLine
from app.schemas.search import (
    RewriteApplyResponse,
    RewriteChange,
    RewritePreviewResponse,
    RewriteRequest,
    SearchResponse,
    SearchResult,
    StructuralMatch,
    StructuralQuery,
    StructuralSearchResponse,
)
from app.services.structural_search import match_structural, rewrite_wordlines

router = APIRouter(prefix="/search", tags=["search"])

# Searchable fields on WordLine
_WL_FIELDS = ("form", "lemma", "upos", "xpos", "feats", "head", "deprel", "deps", "misc")


def _apply_filters(stmt, filters, sent_id, text, treebank_title):
    """Apply search filters to a statement."""
    for field_name, value in filters.items():
        if value is not None:
            stmt = stmt.where(getattr(WordLine, field_name).ilike(f"%{value}%"))
    if sent_id is not None:
        stmt = stmt.where(Sentence.sent_id.ilike(f"%{sent_id}%"))
    if text is not None:
        stmt = stmt.where(Sentence.text.ilike(f"%{text}%"))
    if treebank_title is not None:
        stmt = stmt.where(Treebank.title.ilike(f"%{treebank_title}%"))
    return stmt


@router.get("", response_model=SearchResponse)
async def search(
    form: str | None = None,
    lemma: str | None = None,
    upos: str | None = None,
    xpos: str | None = None,
    feats: str | None = None,
    head: str | None = None,
    deprel: str | None = None,
    deps: str | None = None,
    misc: str | None = None,
    sent_id: str | None = None,
    text: str | None = None,
    treebank_title: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    filters = {
        "form": form,
        "lemma": lemma,
        "upos": upos,
        "xpos": xpos,
        "feats": feats,
        "head": head,
        "deprel": deprel,
        "deps": deps,
        "misc": misc,
    }

    def base_joins(s):
        return (
            s.join(Annotation, WordLine.annotation_id == Annotation.id)
            .join(Sentence, Annotation.sentence_id == Sentence.id)
            .join(Treebank, Sentence.treebank_id == Treebank.id)
            .join(User, Annotation.annotator_id == User.id)
        )

    # Count query
    count_stmt = base_joins(select(func.count(WordLine.id)))
    count_stmt = _apply_filters(count_stmt, filters, sent_id, text, treebank_title)
    total = (await db.execute(count_stmt)).scalar_one()

    # Data query
    stmt = base_joins(select(WordLine)).options(
        selectinload(WordLine.annotation)
        .selectinload(Annotation.sentence)
        .selectinload(Sentence.treebank),
        selectinload(WordLine.annotation).selectinload(Annotation.annotator),
    )
    stmt = _apply_filters(stmt, filters, sent_id, text, treebank_title)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    wordlines = result.scalars().all()

    return SearchResponse(
        total=total,
        results=[
            SearchResult(
                id=wl.id,
                annotation_id=wl.annotation_id,
                id_f=wl.id_f,
                form=wl.form,
                lemma=wl.lemma,
                upos=wl.upos,
                xpos=wl.xpos,
                feats=wl.feats,
                head=wl.head,
                deprel=wl.deprel,
                deps=wl.deps,
                misc=wl.misc,
                sentence_sent_id=wl.annotation.sentence.sent_id,
                sentence_text=wl.annotation.sentence.text,
                treebank_title=wl.annotation.sentence.treebank.title,
                annotator_username=wl.annotation.annotator.username,
            )
            for wl in wordlines
        ],
    )


@router.post("/structural", response_model=StructuralSearchResponse)
async def structural_search(
    query: StructuralQuery,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Search for tokens matching structural (tree-pattern) constraints.

    The search operates on template annotations and returns sentences that
    contain at least one token matching all specified constraints (target
    properties, head constraints, dependent constraints, negated dependents).

    Pagination is by sentence, not by individual token match.
    """
    # Build base query: sentences with their template annotation wordlines
    stmt = (
        select(Sentence)
        .join(Annotation, Annotation.sentence_id == Sentence.id)
        .where(Annotation.is_template.is_(True))
        .options(
            selectinload(Sentence.treebank),
            selectinload(Sentence.annotations.and_(Annotation.is_template.is_(True))).selectinload(
                Annotation.wordlines
            ),
        )
    )

    if query.treebank_id is not None:
        stmt = stmt.where(Sentence.treebank_id == query.treebank_id)

    # Order deterministically for stable pagination
    stmt = stmt.order_by(Sentence.treebank_id, Sentence.order)

    result = await db.execute(stmt)
    sentences = result.scalars().unique().all()

    # Convert the query model to a plain dict for the matcher
    query_dict = query.model_dump(exclude={"treebank_id", "limit", "offset"})

    # Run structural matching on each sentence
    matches: list[StructuralMatch] = []
    for sent in sentences:
        # Find the template annotation
        template = next((a for a in sent.annotations if a.is_template), None)
        if template is None or not template.wordlines:
            continue

        # Convert ORM wordlines to dicts
        wl_dicts = [
            {
                "id_f": wl.id_f,
                "form": wl.form,
                "lemma": wl.lemma,
                "upos": wl.upos,
                "xpos": wl.xpos,
                "feats": wl.feats,
                "head": wl.head,
                "deprel": wl.deprel,
                "deps": wl.deps,
                "misc": wl.misc,
            }
            for wl in template.wordlines
        ]

        matched_tokens = match_structural(query_dict, wl_dicts)
        if matched_tokens:
            matches.append(
                StructuralMatch(
                    sentence_id=sent.id,
                    sent_id=sent.sent_id,
                    text=sent.text,
                    treebank_id=sent.treebank_id,
                    treebank_title=sent.treebank.title,
                    matched_token_ids=[t["id_f"] for t in matched_tokens],
                )
            )

    total = len(matches)
    paginated = matches[query.offset : query.offset + query.limit]

    return StructuralSearchResponse(results=paginated, total=total)


# ---------------------------------------------------------------------------
# Batch rewrite endpoints
# ---------------------------------------------------------------------------


def _wl_dicts_from_annotation(annotation) -> list[dict[str, str]]:
    """Convert ORM wordlines to dicts."""
    return [
        {
            "id_f": wl.id_f,
            "form": wl.form,
            "lemma": wl.lemma,
            "upos": wl.upos,
            "xpos": wl.xpos,
            "feats": wl.feats,
            "head": wl.head,
            "deprel": wl.deprel,
            "deps": wl.deps,
            "misc": wl.misc,
        }
        for wl in annotation.wordlines
    ]


async def _fetch_annotations_for_rewrite(
    db: AsyncSession,
    treebank_id: int | None,
    scope: str,
    current_user: User,
) -> list[tuple[Sentence, Annotation]]:
    """Fetch sentence+annotation pairs for rewriting."""
    stmt = (
        select(Sentence)
        .join(Annotation, Annotation.sentence_id == Sentence.id)
        .options(
            selectinload(Sentence.treebank),
            selectinload(Sentence.annotations).selectinload(Annotation.wordlines),
        )
    )

    if treebank_id is not None:
        stmt = stmt.where(Sentence.treebank_id == treebank_id)

    if scope == "template":
        stmt = stmt.where(Annotation.is_template.is_(True))
    elif scope == "mine":
        stmt = stmt.where(Annotation.annotator_id == current_user.id)

    stmt = stmt.order_by(Sentence.treebank_id, Sentence.order)
    result = await db.execute(stmt)
    sentences = result.scalars().unique().all()

    pairs = []
    for sent in sentences:
        for ann in sent.annotations:
            if scope == "template" and not ann.is_template:
                continue
            if scope == "mine" and ann.annotator_id != current_user.id:
                continue
            if ann.wordlines:
                pairs.append((sent, ann))
    return pairs


@router.post("/rewrite/preview", response_model=RewritePreviewResponse)
async def preview_rewrite(
    body: RewriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview batch rewrite operations across matching annotations.

    Returns the list of changes that would be applied without actually
    modifying any data. Use POST /rewrite/apply to commit changes.
    """
    pairs = await _fetch_annotations_for_rewrite(
        db, body.treebank_id, body.annotation_scope, current_user
    )

    all_changes: list[RewriteChange] = []
    affected_sentences = set()

    for sent, ann in pairs:
        wl_dicts = _wl_dicts_from_annotation(ann)
        _, changes = rewrite_wordlines(
            wl_dicts,
            body.pattern,
            body.operations,
            sent_id=sent.sent_id,
            text=sent.text or "",
        )
        for change in changes:
            all_changes.append(
                RewriteChange(
                    sentence_id=sent.id,
                    sent_id=sent.sent_id,
                    token_id=change["token_id"],
                    form=change["form"],
                    node_name=change["node_name"],
                    descriptions=change["descriptions"],
                )
            )
            affected_sentences.add(sent.id)

    return RewritePreviewResponse(
        changes=all_changes,
        total_tokens=len(all_changes),
        total_sentences=len(affected_sentences),
    )


@router.post("/rewrite/apply", response_model=RewriteApplyResponse)
async def apply_rewrite(
    body: RewriteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply batch rewrite operations to matching annotations.

    Modifies wordlines in-place for annotations the user owns. Template
    annotations can only be rewritten by the user who uploaded them (or any
    user if annotation_scope='template' — use with care).
    """
    pairs = await _fetch_annotations_for_rewrite(
        db, body.treebank_id, body.annotation_scope, current_user
    )

    all_changes: list[RewriteChange] = []
    applied = 0
    skipped = 0

    for sent, ann in pairs:
        # Skip annotations in submitted/approved state
        if ann.status in (AnnotationStatus.SUBMITTED, AnnotationStatus.APPROVED):
            skipped += 1
            continue

        wl_dicts = _wl_dicts_from_annotation(ann)
        modified_wls, changes = rewrite_wordlines(
            wl_dicts,
            body.pattern,
            body.operations,
            sent_id=sent.sent_id,
            text=sent.text or "",
        )

        if not changes:
            continue

        for change in changes:
            all_changes.append(
                RewriteChange(
                    sentence_id=sent.id,
                    sent_id=sent.sent_id,
                    token_id=change["token_id"],
                    form=change["form"],
                    node_name=change["node_name"],
                    descriptions=change["descriptions"],
                )
            )

        # Persist: delete old wordlines, insert modified ones
        await db.execute(delete(WordLine).where(WordLine.annotation_id == ann.id))
        for wl_dict in modified_wls:
            wl = WordLine(
                annotation_id=ann.id,
                id_f=wl_dict["id_f"],
                form=wl_dict["form"],
                lemma=wl_dict["lemma"],
                upos=wl_dict["upos"],
                xpos=wl_dict["xpos"],
                feats=wl_dict["feats"],
                head=wl_dict["head"],
                deprel=wl_dict["deprel"],
                deps=wl_dict["deps"],
                misc=wl_dict["misc"],
            )
            wl.populate_parsed_fields()
            db.add(wl)

        # Mark annotation as DRAFT if it was NEW
        if ann.status == AnnotationStatus.NEW:
            ann.status = AnnotationStatus.DRAFT

        applied += 1

    await db.commit()

    return RewriteApplyResponse(
        applied=applied,
        skipped=skipped,
        changes=all_changes,
    )
