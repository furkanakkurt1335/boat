from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.annotation import Annotation
from app.models.sentence import Sentence
from app.models.treebank import Treebank
from app.models.user import User
from app.models.wordline import WordLine
from app.schemas.annotation import AnnotationRead
from app.schemas.sentence import SentenceCreate, SentenceRead
from app.services.conllu import FIELDS

router = APIRouter(prefix="/sentences", tags=["sentences"])


@router.get("/{sentence_id}", response_model=SentenceRead)
async def get_sentence(
    sentence_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sentence).where(Sentence.id == sentence_id))
    sentence = result.scalar_one_or_none()
    if not sentence:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sentence not found")
    return sentence


@router.post("", response_model=SentenceRead, status_code=status.HTTP_201_CREATED)
async def create_sentence(
    treebank_id: int,
    body: SentenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Treebank).where(Treebank.id == treebank_id))
    treebank = result.scalar_one_or_none()
    if not treebank:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treebank not found")

    # Auto-increment order
    max_order_result = await db.execute(
        select(func.max(Sentence.order)).where(Sentence.treebank_id == treebank_id)
    )
    next_order = (max_order_result.scalar() or 0) + 1

    sentence = Sentence(
        order=next_order,
        treebank_id=treebank_id,
        sent_id=body.sent_id or f"{treebank.title}-{next_order}",
        text=body.text,
        metadata_=body.metadata,
    )
    db.add(sentence)
    await db.flush()

    # Create template annotation with default wordlines from tokenized text
    annotation = Annotation(
        annotator_id=current_user.id,
        sentence_id=sentence.id,
        is_template=True,
        status=0,
    )
    db.add(annotation)
    await db.flush()

    tokens = body.text.split()
    for i, token in enumerate(tokens, start=1):
        wordline = WordLine(
            annotation_id=annotation.id,
            id_f=str(i),
            form=token,
            lemma="_",
            upos="_",
            xpos="_",
            feats="_",
            head="_",
            deprel="_",
            deps="_",
            misc="_",
        )
        db.add(wordline)

    await db.commit()
    await db.refresh(sentence)
    return sentence


@router.delete("/{sentence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sentence(
    sentence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sentence).where(Sentence.id == sentence_id))
    sentence = result.scalar_one_or_none()
    if not sentence:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sentence not found")
    tb_result = await db.execute(select(Treebank).where(Treebank.id == sentence.treebank_id))
    treebank = tb_result.scalar_one_or_none()
    if current_user.id != treebank.created_by:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to perform this action")
    await db.delete(sentence)
    await db.commit()


@router.get("/{sentence_id}/annotations", response_model=list[AnnotationRead])
async def list_sentence_annotations(
    sentence_id: int,
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Annotation)
        .where(Annotation.sentence_id == sentence_id)
        .options(selectinload(Annotation.annotator))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    annotations = result.scalars().all()
    return [
        AnnotationRead(
            id=a.id,
            annotator_id=a.annotator_id,
            sentence_id=a.sentence_id,
            notes=a.notes,
            status=a.status,
            is_template=a.is_template,
            is_gold=a.is_gold,
            created_at=a.created_at,
            annotator_username=a.annotator.username,
        )
        for a in annotations
    ]


@router.get("/{sentence_id}/diff")
async def diff_annotations(
    sentence_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Compare all non-template annotations for a sentence, field by field.

    Returns a per-token comparison showing each annotator's values and
    which fields disagree.
    """
    result = await db.execute(
        select(Annotation)
        .where(
            Annotation.sentence_id == sentence_id,
            Annotation.is_template.is_(False),
        )
        .options(
            selectinload(Annotation.wordlines),
            selectinload(Annotation.annotator),
        )
    )
    annotations = result.scalars().all()

    if len(annotations) < 2:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Need at least 2 annotations to compare",
        )

    # Build per-annotator wordline maps keyed by id_f
    annotators: list[dict] = []
    for anno in annotations:
        wl_map = {}
        for wl in anno.wordlines:
            wl_map[wl.id_f] = {f: getattr(wl, f) for f in FIELDS}
            wl_map[wl.id_f]["id_f"] = wl.id_f
        annotators.append(
            {
                "annotation_id": anno.id,
                "username": anno.annotator.username,
                "status": anno.status,
                "wordlines": wl_map,
            }
        )

    # Collect all token IDs across annotators
    all_ids: set[str] = set()
    for a in annotators:
        all_ids.update(a["wordlines"].keys())

    # Compare fields per token
    compared_fields = ("form", "lemma", "upos", "xpos", "feats", "head", "deprel", "deps", "misc")
    tokens: list[dict] = []
    disagreement_count = 0

    for token_id in sorted(all_ids, key=_sort_key):
        values_by_annotator = []
        disagreements: list[str] = []

        for a in annotators:
            wl = a["wordlines"].get(token_id)
            values_by_annotator.append(
                {
                    "username": a["username"],
                    "annotation_id": a["annotation_id"],
                    "values": wl,
                }
            )

        # Check each field for disagreement
        for field in compared_fields:
            field_values = set()
            for a in annotators:
                wl = a["wordlines"].get(token_id)
                if wl:
                    field_values.add(wl[field])
            if len(field_values) > 1:
                disagreements.append(field)

        if disagreements:
            disagreement_count += 1

        tokens.append(
            {
                "id_f": token_id,
                "annotators": values_by_annotator,
                "disagreements": disagreements,
            }
        )

    return {
        "sentence_id": sentence_id,
        "annotator_count": len(annotators),
        "token_count": len(tokens),
        "disagreement_count": disagreement_count,
        "tokens": tokens,
    }


def _sort_key(token_id: str) -> tuple[int, int]:
    """Sort CoNLL-U token IDs: '1' < '1-2' < '2' < '3'."""
    if "-" in token_id:
        parts = token_id.split("-")
        return (int(parts[0]), 0)
    return (int(token_id), 1)
