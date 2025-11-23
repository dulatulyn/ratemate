from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import aliased

from ratemate_app.models.follow import Follow
from ratemate_app.models.user import User

async def follow_user(db: AsyncSession, follower_id: int, followed_id: int) -> Follow:
    if follower_id == followed_id:
        raise ValueError("Cannot follow self")
    
    existing = await db.execute(select(Follow).where(Follow.follower_id == follower_id, Follow.followed_id == followed_id))
    row = existing.scalar_one_or_none()

    if row:
        return row
    
    f = Follow(follower_id=follower_id, followed_id=followed_id)
    db.add(f)

    await db.commit()
    await db.refresh(f)

    return f

async def unfollow_user(db: AsyncSession, follower_id: int, followed_id: int) -> None:
    await db.execute(delete(Follow).where(Follow.follower_id == follower_id, Follow.followed_id == followed_id))
    await db.commit()

async def list_following(db: AsyncSession, user_id: int) -> list[User]:
    result = await db.execute(
        select(User).join(Follow, Follow.followed_id == User.id).where(Follow.follower_id == user_id)
    )
    return result.scalars().all()

async def list_followers(db: AsyncSession, user_id: int) -> list[User]:
    result = await db.execute(
        select(User).join(Follow, Follow.follower_id == User.id).where(Follow.followed_id == user_id)
    )
    return result.scalars().all()

async def list_common_following(db: AsyncSession, user_id_a: int, user_id_b: int) -> list[User]:
    F1 = aliased(Follow)
    F2 = aliased(Follow)

    result = await db.execute(
        select(User).join(F1, F1.followed_id == User.id)
        .join(F2, F2.followed_id == User.id)
        .where(F1.follower_id == user_id_a, F2.follower_id == user_id_b)
    )

    return result.scalars().all()