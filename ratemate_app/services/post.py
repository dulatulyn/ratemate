from sqlalchemy.ext.asyncio import AsyncSession
from ratemate_app.models.post import Post
from ratemate_app.schemas.post import PostCreate

async def create_post(db: AsyncSession, owner_id: int, data: PostCreate) -> Post:
    post = Post(owner_id=owner_id, title=data.title, content=data.content)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post