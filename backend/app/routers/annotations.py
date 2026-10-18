from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.annotation import Annotation, AnnotationStatus
from app.models.sentence import Sentence
from app.models.user import User
from app.schemas.annotation import (
    AnnotationCreate,
    AnnotationDetail,
    AnnotationRead,
    AnnotationUpdate,
)
from app.services.wordlines import copy_wordlines

# Valid status transitions: {(from_status, to_status)}
_ANNOTATOR_TRANSITIONS = {
    (AnnotationStatus.NEW, AnnotationStatus.DRAFT),
    (AnnotationStatus.DRAFT, AnnotationStatus.SUBMITTED),
    (AnnotationStatus.REJECTED, AnnotationStatus.DRAFT),
}
_REVIEWER_TRANSITIONS = {
    (AnnotationStatus.SUBMITTED, AnnotationStatus.APPROVED),
    (AnnotationStatus.SUBMITTED, AnnotationStatus.REJECTED),
}

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.post("", response_model=AnnotationRead, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    body: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify sentence exists
    result = await db.execute(select(Sentence).where(Sentence.id == body.sentence_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sentence not found")

    annotation = Annotation(
        annotator_id=current_user.id,
        sentence_id=body.sentence_id,
        notes=body.notes,
        status=body.status,
        is_template=body.is_template,
    )
    db.add(annotation)

    # Copy wordlines from template annotation if one exists
    template_result = await db.execute(
        select(Annotation)
        .where(
            Annotation.sentence_id == body.sentence_id,
            Annotation.is_template.is_(True),
        )
        .options(selectinload(Annotation.wordlines))
        .limit(1)
    )
    template = template_result.scalar_one_or_none()
    await db.flush()

    if template and template.wordlines:
        db.add_all(copy_wordlines(template.wordlines, annotation.id))

    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.post("/{annotation_id}/clone", response_model=AnnotationRead)
async def clone_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Copy wordlines from another annotation into the current user's annotation.

    Finds the current user's annotation for the same sentence and replaces
    its wordlines with copies from the source annotation.
    """
    # Load the source annotation with its wordlines
    result = await db.execute(
        select(Annotation)
        .where(Annotation.id == annotation_id)
        .options(selectinload(Annotation.wordlines))
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source annotation not found")

    # Find the current user's annotation for this sentence
    target_result = await db.execute(
        select(Annotation)
        .where(
            Annotation.sentence_id == source.sentence_id,
            Annotation.annotator_id == current_user.id,
            Annotation.is_template.is_(False),
        )
        .options(selectinload(Annotation.wordlines))
    )
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "You don't have an annotation for this sentence yet",
        )

    # Delete existing wordlines from target
    for wl in target.wordlines:
        await db.delete(wl)
    await db.flush()

    # Copy wordlines from source
    if source.wordlines:
        db.add_all(copy_wordlines(source.wordlines, target.id))

    await db.commit()
    await db.refresh(target)
    return target


@router.get(
    "/by-position/",
    response_model=AnnotationDetail,
)
async def get_annotation_by_position(
    treebank_id: int,
    order: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get (or create) the current user's annotation for a sentence at a given order."""
    # Find the sentence
    result = await db.execute(
        select(Sentence).where(
            Sentence.treebank_id == treebank_id,
            Sentence.order == order,
        )
    )
    sentence = result.scalar_one_or_none()
    if not sentence:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sentence not found at this position")

    # Find user's annotation for this sentence
    result = await db.execute(
        select(Annotation)
        .where(
            Annotation.sentence_id == sentence.id,
            Annotation.annotator_id == current_user.id,
            Annotation.is_template.is_(False),
        )
        .options(
            selectinload(Annotation.wordlines),
            selectinload(Annotation.annotator),
            selectinload(Annotation.sentence).selectinload(Sentence.treebank),
        )
        .limit(1)
    )
    annotation = result.scalar_one_or_none()

    if not annotation:
        # Auto-create from template
        annotation = Annotation(
            annotator_id=current_user.id,
            sentence_id=sentence.id,
            status=0,
        )
        db.add(annotation)

        # Copy wordlines from template
        tmpl_result = await db.execute(
            select(Annotation)
            .where(
                Annotation.sentence_id == sentence.id,
                Annotation.is_template.is_(True),
            )
            .options(selectinload(Annotation.wordlines))
            .limit(1)
        )
        template = tmpl_result.scalar_one_or_none()
        await db.flush()

        if template and template.wordlines:
            db.add_all(copy_wordlines(template.wordlines, annotation.id))

        await db.commit()

        # Reload with relationships
        result = await db.execute(
            select(Annotation)
            .where(Annotation.id == annotation.id)
            .options(
                selectinload(Annotation.wordlines),
                selectinload(Annotation.annotator),
                selectinload(Annotation.sentence).selectinload(Sentence.treebank),
            )
        )
        annotation = result.scalar_one()

    return _build_annotation_detail(annotation)


@router.get("/{annotation_id}", response_model=AnnotationDetail)
async def get_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Annotation)
        .where(Annotation.id == annotation_id)
        .options(
            selectinload(Annotation.wordlines),
            selectinload(Annotation.annotator),
            selectinload(Annotation.sentence).selectinload(Sentence.treebank),
        )
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annotation not found")

    return _build_annotation_detail(annotation)


@router.patch("/{annotation_id}", response_model=AnnotationRead)
async def update_annotation(
    annotation_id: int,
    body: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Annotation)
        .where(Annotation.id == annotation_id)
        .options(selectinload(Annotation.sentence).selectinload(Sentence.treebank))
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annotation not found")

    # Validate status transitions
    if body.status is not None and body.status != annotation.status:
        old_status = AnnotationStatus(annotation.status)
        new_status = AnnotationStatus(body.status)
        transition = (old_status, new_status)
        treebank = annotation.sentence.treebank

        if transition in _REVIEWER_TRANSITIONS:
            # Only the treebank creator can approve/reject
            if current_user.id != treebank.created_by:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN,
                    "Only the treebank creator can approve or reject annotations",
                )
        elif transition in _ANNOTATOR_TRANSITIONS:
            # Only the annotator can make annotator transitions
            if annotation.annotator_id != current_user.id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your annotation")
        else:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Invalid status transition from {old_status.name} to {new_status.name}",
            )
    elif annotation.annotator_id != current_user.id:
        # For non-status updates, only the annotator can edit
        treebank = annotation.sentence.treebank
        if current_user.id != treebank.created_by:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your annotation")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(annotation, field, value)
    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Annotation).where(Annotation.id == annotation_id))
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annotation not found")
    if annotation.annotator_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your annotation")
    await db.delete(annotation)
    await db.commit()


@router.get("/mine/", response_model=list[AnnotationDetail])
async def my_annotations(
    annotation_status: int | None = Query(None, alias="status"),
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Annotation)
        .where(Annotation.annotator_id == current_user.id, Annotation.is_template.is_(False))
        .options(
            selectinload(Annotation.wordlines),
            selectinload(Annotation.annotator),
            selectinload(Annotation.sentence).selectinload(Sentence.treebank),
        )
        .order_by(Annotation.created_at.desc())
    )
    if annotation_status is not None:
        stmt = stmt.where(Annotation.status == annotation_status)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    annotations = result.scalars().all()

    return [_build_annotation_detail(a) for a in annotations]


def _build_annotation_detail(a: Annotation) -> AnnotationDetail:
    """Build an AnnotationDetail from a loaded Annotation with relationships."""
    return AnnotationDetail(
        id=a.id,
        annotator_id=a.annotator_id,
        sentence_id=a.sentence_id,
        notes=a.notes,
        status=a.status,
        is_template=a.is_template,
        is_gold=a.is_gold,
        created_at=a.created_at,
        wordlines=[
            {
                "id": wl.id,
                "annotation_id": wl.annotation_id,
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
                "feats_parsed": wl.feats_parsed,
                "misc_parsed": wl.misc_parsed,
            }
            for wl in a.wordlines
        ],
        annotator_username=a.annotator.username,
        sentence_sent_id=a.sentence.sent_id,
        sentence_text=a.sentence.text,
        sentence_metadata=a.sentence.metadata_,
        treebank_title=a.sentence.treebank.title,
        treebank_id=a.sentence.treebank.id,
        treebank_created_by=a.sentence.treebank.created_by,
        sentence_order=a.sentence.order,
    )
