from collections.abc import AsyncIterator
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import case
from starlette.responses import JSONResponse, StreamingResponse

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.annotation import Annotation, AnnotationStatus
from app.models.sentence import Sentence
from app.models.treebank import Treebank
from app.models.user import User
from app.models.validation_profile import ValidationProfile
from app.models.wordline import WordLine
from app.schemas.sentence import SentenceBrief
from app.schemas.treebank import TreebankCreate, TreebankRead, TreebankWithProgress
from app.services.agreement import (
    compute_annotation_agreement,
    get_cached_agreement,
    set_cached_agreement,
)
from app.services.conllu import (
    LANGUAGES,
    _format_sentence_block,
    parse_text,
    validate_uploaded_text,
)


class ExportFormat(StrEnum):
    conllu = "conllu"
    json = "json"


router = APIRouter(prefix="/treebanks", tags=["treebanks"])


@router.get("", response_model=list[TreebankWithProgress])
async def list_treebanks(
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    # Compute progress stats in a single query
    stmt = (
        select(
            Treebank,
            func.count(func.distinct(Sentence.id)).label("sentence_count"),
            func.count(Annotation.id).label("annotation_count"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            Annotation.status.in_(
                                [
                                    AnnotationStatus.SUBMITTED,
                                    AnnotationStatus.APPROVED,
                                ]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("complete_count"),
        )
        .outerjoin(Sentence, Sentence.treebank_id == Treebank.id)
        .outerjoin(Annotation, Annotation.sentence_id == Sentence.id)
        .group_by(Treebank.id)
        .order_by(Treebank.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        TreebankWithProgress(
            id=tb.id,
            title=tb.title,
            language=tb.language,
            created_by=tb.created_by,
            created_at=tb.created_at,
            sentence_count=sent_count or 0,
            annotation_count=anno_count or 0,
            complete_count=comp_count or 0,
        )
        for tb, sent_count, anno_count, comp_count in rows
    ]


@router.post("", response_model=TreebankRead, status_code=status.HTTP_201_CREATED)
async def create_treebank(
    body: TreebankCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Treebank).where(Treebank.title == body.title))
    if result.scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Treebank title already exists")
    treebank = Treebank(title=body.title, language=body.language, created_by=current_user.id)
    db.add(treebank)
    await db.flush()

    # Auto-create a validation profile with sensible MISC defaults
    profile = ValidationProfile(
        treebank_id=treebank.id,
        allowed_misc={
            "SpaceAfter": ["No"],
            "SpacesAfter": None,
            "Translit": None,
            "LTranslit": None,
            "Gloss": None,
        },
    )
    db.add(profile)
    await db.commit()
    await db.refresh(treebank)
    return treebank


@router.get("/languages")
async def list_languages(_current_user: User = Depends(get_current_user)):
    return LANGUAGES


@router.get("/by-title/{title}", response_model=TreebankRead)
async def get_treebank_by_title(
    title: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Treebank).where(Treebank.title == title))
    treebank = result.scalar_one_or_none()
    if not treebank:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treebank not found")
    return treebank


@router.get("/{treebank_id}", response_model=TreebankRead)
async def get_treebank(
    treebank_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Treebank).where(Treebank.id == treebank_id))
    treebank = result.scalar_one_or_none()
    if not treebank:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treebank not found")
    return treebank


@router.get("/{treebank_id}/stats")
async def treebank_stats(
    treebank_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Corpus statistics for a treebank (based on template annotations)."""
    # Verify treebank exists
    result = await db.execute(select(Treebank).where(Treebank.id == treebank_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treebank not found")

    # UPOS distribution
    upos_stmt = (
        select(WordLine.upos, func.count().label("cnt"))
        .join(Annotation, Annotation.id == WordLine.annotation_id)
        .join(Sentence, Sentence.id == Annotation.sentence_id)
        .where(
            Sentence.treebank_id == treebank_id,
            Annotation.is_template.is_(True),
            ~WordLine.id_f.contains("."),
            ~WordLine.id_f.contains("-"),
        )
        .group_by(WordLine.upos)
        .order_by(desc("cnt"))
    )
    upos_rows = (await db.execute(upos_stmt)).all()
    upos_distribution = {tag: count for tag, count in upos_rows if tag != "_"}

    # DEPREL distribution
    deprel_stmt = (
        select(WordLine.deprel, func.count().label("cnt"))
        .join(Annotation, Annotation.id == WordLine.annotation_id)
        .join(Sentence, Sentence.id == Annotation.sentence_id)
        .where(
            Sentence.treebank_id == treebank_id,
            Annotation.is_template.is_(True),
            ~WordLine.id_f.contains("."),
            ~WordLine.id_f.contains("-"),
        )
        .group_by(WordLine.deprel)
        .order_by(desc("cnt"))
    )
    deprel_rows = (await db.execute(deprel_stmt)).all()
    deprel_distribution = {rel: count for rel, count in deprel_rows if rel != "_"}

    # Top 20 lemmas
    lemma_stmt = (
        select(WordLine.lemma, func.count().label("cnt"))
        .join(Annotation, Annotation.id == WordLine.annotation_id)
        .join(Sentence, Sentence.id == Annotation.sentence_id)
        .where(
            Sentence.treebank_id == treebank_id,
            Annotation.is_template.is_(True),
            ~WordLine.id_f.contains("."),
            ~WordLine.id_f.contains("-"),
            WordLine.lemma != "_",
        )
        .group_by(WordLine.lemma)
        .order_by(desc("cnt"))
        .limit(20)
    )
    lemma_rows = (await db.execute(lemma_stmt)).all()
    top_lemmas = [{"lemma": lemma, "count": count} for lemma, count in lemma_rows]

    # Sentence lengths (token count per sentence, excluding MWTs and empty nodes)
    sent_len_stmt = (
        select(func.count(WordLine.id).label("token_count"))
        .join(Annotation, Annotation.id == WordLine.annotation_id)
        .join(Sentence, Sentence.id == Annotation.sentence_id)
        .where(
            Sentence.treebank_id == treebank_id,
            Annotation.is_template.is_(True),
            ~WordLine.id_f.contains("."),
            ~WordLine.id_f.contains("-"),
        )
        .group_by(Sentence.id)
    )
    sent_len_rows = (await db.execute(sent_len_stmt)).all()
    sentence_lengths = [row.token_count for row in sent_len_rows]

    # Total tokens
    total_tokens = sum(upos_distribution.values()) if upos_distribution else 0

    # Total sentences
    total_sentences = len(sentence_lengths)

    return {
        "upos_distribution": upos_distribution,
        "deprel_distribution": deprel_distribution,
        "top_lemmas": top_lemmas,
        "sentence_lengths": sentence_lengths,
        "total_tokens": total_tokens,
        "total_sentences": total_sentences,
    }


@router.delete("/{treebank_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_treebank(
    treebank_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Treebank).where(Treebank.id == treebank_id))
    treebank = result.scalar_one_or_none()
    if not treebank:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treebank not found")
    if current_user.id != treebank.created_by:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to perform this action")
    await db.delete(treebank)
    await db.commit()


@router.get("/{treebank_id}/sentences", response_model=list[SentenceBrief])
async def list_sentences(
    treebank_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Sentence).where(Sentence.treebank_id == treebank_id).order_by(Sentence.order)
    )
    return result.scalars().all()


@router.post("/{treebank_id}/upload", status_code=status.HTTP_201_CREATED)
async def upload_conllu(
    treebank_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Treebank).where(Treebank.id == treebank_id))
    treebank = result.scalar_one_or_none()
    if not treebank:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treebank not found")
    if current_user.id != treebank.created_by:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not authorized to perform this action")

    max_size = 10 * 1024 * 1024  # 10 MB
    raw = await file.read()
    if len(raw) > max_size:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File too large ({len(raw) / 1024 / 1024:.1f} MB). Maximum is 10 MB.",
        )
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "File is not valid UTF-8",
        ) from err
    content = content.replace("\r\n", "\n")
    if not content.endswith("\n"):
        content += "\n"
    if not validate_uploaded_text(content):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid CoNLL-U file")

    sentences = parse_text(content)

    # Get current max order
    max_order_result = await db.execute(
        select(func.max(Sentence.order)).where(Sentence.treebank_id == treebank_id)
    )
    current_max = max_order_result.scalar() or 0

    created_count = 0
    for i, sent_data in enumerate(sentences, start=current_max + 1):
        sent_id = sent_data.get("sent_id", f"{treebank.title}-{i}")
        text = sent_data.get("text", "")
        metadata = sent_data.get("metadata")

        sentence = Sentence(
            order=i,
            treebank_id=treebank_id,
            sent_id=sent_id,
            text=text,
            metadata_=metadata,
        )
        db.add(sentence)
        await db.flush()

        # Create template annotation with wordlines
        annotation = Annotation(
            annotator_id=current_user.id,
            sentence_id=sentence.id,
            is_template=True,
            status=0,
        )
        db.add(annotation)
        await db.flush()

        # Create wordlines from parsed data
        for word_id, fields in sent_data.items():
            if word_id in ("sent_id", "text", "metadata"):
                continue
            wordline = WordLine(
                annotation_id=annotation.id,
                id_f=word_id,
                form=fields.get("form", "_"),
                lemma=fields.get("lemma", "_"),
                upos=fields.get("upos", "_"),
                xpos=fields.get("xpos", "_"),
                feats=fields.get("feats", "_"),
                head=fields.get("head", "_"),
                deprel=fields.get("deprel", "_"),
                deps=fields.get("deps", "_"),
                misc=fields.get("misc", "_"),
            )
            wordline.populate_parsed_fields()
            db.add(wordline)
        created_count += 1

    await db.commit()
    return {"sentences_created": created_count}


def _annotation_matches(
    anno: Annotation,
    *,
    annotator_id: int | None,
    current_user_id: int,
) -> bool:
    """Check whether an annotation matches the export filter criteria.

    If *annotator_id* is given, select that user's non-template annotations.
    Otherwise fall back to the current user's annotations (original behaviour).
    """
    if annotator_id is not None:
        return anno.annotator_id == annotator_id and not anno.is_template
    return anno.annotator_id == current_user_id


def _sentence_to_export_dict(sent: Sentence, anno: Annotation) -> dict:
    """Convert a sentence + annotation pair into a serialisable dict."""
    return {
        "sent_id": sent.sent_id,
        "text": sent.text,
        "metadata": sent.metadata_,
        "wordlines": [
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
            for wl in anno.wordlines
        ],
    }


@router.get("/{treebank_id}/export")
async def export_treebank(
    treebank_id: int,
    format: ExportFormat = Query(ExportFormat.conllu, description="Export format"),
    annotator_id: int | None = Query(
        None,
        description="Export a specific annotator's (non-template) annotations. "
        "If omitted, exports the current user's annotations.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Treebank).where(Treebank.id == treebank_id))
    treebank = result.scalar_one_or_none()
    if not treebank:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treebank not found")

    # Validate annotator_id if provided
    if annotator_id is not None:
        user_result = await db.execute(select(User).where(User.id == annotator_id))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Annotator not found")

    # Fetch sentences with annotations and wordlines
    stmt = (
        select(Sentence)
        .where(Sentence.treebank_id == treebank_id)
        .options(selectinload(Sentence.annotations).selectinload(Annotation.wordlines))
        .order_by(Sentence.order)
    )
    result = await db.execute(stmt)
    sentences = result.scalars().all()

    # Build export data, filtering annotations by the requested criteria
    export_data: list[dict] = []
    for sent in sentences:
        matching = [
            a
            for a in sent.annotations
            if _annotation_matches(a, annotator_id=annotator_id, current_user_id=current_user.id)
        ]
        for anno in matching:
            if not anno.wordlines:
                continue
            export_data.append(_sentence_to_export_dict(sent, anno))

    # --- JSON format ---------------------------------------------------------
    if format == ExportFormat.json:
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f'attachment; filename="{treebank.title}.json"',
            },
        )

    # --- CoNLL-U format (streaming) ------------------------------------------
    async def _stream_conllu() -> AsyncIterator[str]:
        for sent_dict in export_data:
            yield _format_sentence_block(sent_dict)

    return StreamingResponse(
        _stream_conllu(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{treebank.title}.conllu"',
        },
    )


@router.get("/{treebank_id}/agreement")
async def treebank_agreement(
    treebank_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    # Check cache first
    cached = get_cached_agreement(treebank_id)
    if cached is not None:
        return cached

    # Only fetch non-template annotations with the specific wordline fields
    # needed for agreement comparison, filtering at the SQL level.
    stmt = (
        select(
            Annotation.sentence_id,
            Annotation.id,
            WordLine.id_f,
            WordLine.form,
            WordLine.lemma,
            WordLine.upos,
            WordLine.feats,
            WordLine.head,
            WordLine.deprel,
        )
        .join(Sentence, Sentence.id == Annotation.sentence_id)
        .join(WordLine, WordLine.annotation_id == Annotation.id)
        .where(
            Sentence.treebank_id == treebank_id,
            Annotation.is_template.is_(False),
        )
    )
    result = await db.execute(stmt)
    rows = result.all()

    # Pre-index: sentence_id -> annotation_id -> [wordline dicts]
    sentence_annos: dict[int, dict[int, list[dict]]] = {}
    for sentence_id, anno_id, id_f, form, lemma, upos, feats, head, deprel in rows:
        annos = sentence_annos.setdefault(sentence_id, {})
        wl_list = annos.setdefault(anno_id, [])
        wl_list.append(
            {
                "id_f": id_f,
                "form": form,
                "lemma": lemma,
                "upos": upos,
                "feats": feats,
                "head": head,
                "deprel": deprel,
            }
        )

    agreement_sum = 0.0
    scored_count = 0

    for annos_by_id in sentence_annos.values():
        if len(annos_by_id) < 2:
            continue

        wordline_lists = list(annos_by_id.values())

        score = compute_annotation_agreement(wordline_lists)
        if score == -1:
            continue
        agreement_sum += score
        scored_count += 1

    response = {
        "treebank_id": treebank_id,
        "agreement": agreement_sum / scored_count if scored_count else 0,
        "sentences_scored": scored_count,
    }
    set_cached_agreement(treebank_id, response)
    return response
