from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.validation_profile import ValidationProfile
from app.schemas.validation_profile import (
    ValidationProfileCreate,
    ValidationProfileRead,
    ValidationProfileUpdate,
)

router = APIRouter(prefix="/validation-profiles", tags=["validation"])


@router.get("/{treebank_id}", response_model=ValidationProfileRead)
async def get_profile(
    treebank_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ValidationProfile).where(ValidationProfile.treebank_id == treebank_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No validation profile")
    return profile


@router.post("", response_model=ValidationProfileRead, status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: ValidationProfileCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    profile = ValidationProfile(**body.model_dump())
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.patch("/{profile_id}", response_model=ValidationProfileRead)
async def update_profile(
    profile_id: int,
    body: ValidationProfileUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ValidationProfile).where(ValidationProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile
