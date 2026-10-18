from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_admin_user
from app.models.user import User
from app.schemas.auth import UserRead

router = APIRouter(prefix="/admin", tags=["admin"])


class UserListResponse(BaseModel):
    users: list[UserRead]
    total: int


class UserActionRequest(BaseModel):
    user_id: int


@router.get("/users", response_model=UserListResponse)
async def list_users(
    pending_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """List all users, optionally filtered to pending (inactive) only."""
    stmt = select(User)
    if pending_only:
        stmt = stmt.where(User.is_active.is_(False))
    stmt = stmt.order_by(User.id)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return UserListResponse(users=users, total=len(users))


@router.post("/users/approve", response_model=UserRead)
async def approve_user(
    body: UserActionRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """Activate a pending user account."""
    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.is_active:
        raise HTTPException(status.HTTP_409_CONFLICT, "User is already active")
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/users/reject", response_model=UserRead)
async def reject_user(
    body: UserActionRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
):
    """Deactivate a user account."""
    result = await db.execute(select(User).where(User.id == body.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot deactivate an admin")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user
