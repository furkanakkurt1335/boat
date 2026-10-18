from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.guideline import Guideline
from app.models.user import User
from app.schemas.guideline import GuidelineCreate, GuidelineRead, GuidelineUpdate

router = APIRouter(prefix="/treebanks", tags=["guidelines"])


@router.get("/{treebank_id}/guidelines", response_model=list[GuidelineRead])
async def list_guidelines(
    treebank_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Guideline).where(Guideline.treebank_id == treebank_id).order_by(Guideline.key)
    )
    return result.scalars().all()


@router.get(
    "/{treebank_id}/guidelines/{key}",
    response_model=GuidelineRead,
)
async def get_guideline(
    treebank_id: int,
    key: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Guideline).where(Guideline.treebank_id == treebank_id, Guideline.key == key)
    )
    guideline = result.scalar_one_or_none()
    if not guideline:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guideline not found")
    return guideline


@router.post(
    "/{treebank_id}/guidelines",
    response_model=GuidelineRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_guideline(
    treebank_id: int,
    body: GuidelineCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    guideline = Guideline(treebank_id=treebank_id, key=body.key, text=body.text)
    db.add(guideline)
    await db.commit()
    await db.refresh(guideline)
    return guideline


@router.patch(
    "/{treebank_id}/guidelines/{guideline_id}",
    response_model=GuidelineRead,
)
async def update_guideline(
    treebank_id: int,
    guideline_id: int,
    body: GuidelineUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Guideline).where(
            Guideline.id == guideline_id,
            Guideline.treebank_id == treebank_id,
        )
    )
    guideline = result.scalar_one_or_none()
    if not guideline:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guideline not found")
    guideline.text = body.text
    await db.commit()
    await db.refresh(guideline)
    return guideline


@router.delete(
    "/{treebank_id}/guidelines/{guideline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_guideline(
    treebank_id: int,
    guideline_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Guideline).where(
            Guideline.id == guideline_id,
            Guideline.treebank_id == treebank_id,
        )
    )
    guideline = result.scalar_one_or_none()
    if not guideline:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guideline not found")
    await db.delete(guideline)
    await db.commit()
