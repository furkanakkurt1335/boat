from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.comment import Comment
from app.models.sentence import Sentence
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead

router = APIRouter(prefix="/sentences", tags=["comments"])


@router.get("/{sentence_id}/comments", response_model=list[CommentRead])
async def list_comments(
    sentence_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.sentence_id == sentence_id)
        .options(selectinload(Comment.user))
        .order_by(Comment.created_at)
    )
    comments = result.scalars().all()
    return [
        CommentRead(
            id=c.id,
            sentence_id=c.sentence_id,
            user_id=c.user_id,
            username=c.user.username,
            text=c.text,
            created_at=c.created_at,
        )
        for c in comments
    ]


@router.post(
    "/{sentence_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    sentence_id: int,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify sentence exists
    result = await db.execute(select(Sentence).where(Sentence.id == sentence_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sentence not found")

    comment = Comment(
        sentence_id=sentence_id,
        user_id=current_user.id,
        text=body.text,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentRead(
        id=comment.id,
        sentence_id=comment.sentence_id,
        user_id=comment.user_id,
        username=current_user.username,
        text=comment.text,
        created_at=comment.created_at,
    )


@router.delete(
    "/{sentence_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    sentence_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.sentence_id == sentence_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your comment")
    await db.delete(comment)
    await db.commit()
