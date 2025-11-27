from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from ratemate_app.models.post import Post
from ratemate_app.schemas.post import PostCreate

async def create_post(db: AsyncSession, owner_id: int, data: PostCreate) -> Post:
    post = Post(owner_id=owner_id, title=data.title, content=data.content)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post

async def delete_post(db: AsyncSession, post: Post) -> None:
    await db.execute(delete(Post).where(Post.id == post.id))
    await db.commit()