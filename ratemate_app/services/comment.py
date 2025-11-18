from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ratemate_app.models.comment import Comment
from ratemate_app.schemas.comment import CommentCreate

async def create_comment(db: AsyncSession, user_id: int, payload: CommentCreate) -> Comment:
    if payload.parent_id is not None:
        parent = await db.execute(select(Comment). where(Comment.id == payload.parent_id))
        parent_obj = parent.scalar_one_or_none()

        if not parent_obj or parent_obj.post_id != payload.post_id:
            raise ValueError("Invalid parent_id")
        
    comment = Comment(user_id=user_id, post_id=payload.post_id, content=payload.content, parent_id=payload.parent_id)

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return comment

async def list_post_comments(db: AsyncSession, post_id: int) -> list[Comment]:
    result = await db.execute(select(Comment).where(Comment.post_id == post_id))
    return list(result.scalars())