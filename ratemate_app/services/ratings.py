from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ratemate_app.models.rating import Rating

async def set_post_rating(db: AsyncSession, user_id: int, post_id: int, score: int) -> Rating:
    existing = await db.execute(select(Rating).where(Rating.user_id == user_id, Rating.post_id == post_id))
    
    row = existing.scalar_one_or_none()

    if row:
        row.score = score
        await db.commit()
        await db.refresh(row)
        return row
    
    rating = Rating(user_id=user_id, post_id=post_id, score=score)
    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    return rating

async def set_comment_rating(db: AsyncSession, user_id: int, comment_id: int, score: int) -> Rating:
    existing = await db.execute(select(Rating).where(Rating.user_id == user_id, Rating.comment_id == comment_id))
    
    row = existing.scalar_one_or_none()

    if row:
        row.score = score
        await db.commit()
        await db.refresh(row)
        return row
    
    rating = Rating(user_id=user_id, comment_id=comment_id, score=score)
    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    return rating

async def get_post_rating_summary(db: AsyncSession, post_id: int) -> dict:
    q = await db.execute(func.avg(Rating.score), func.count(Rating.id).where(Rating.post_id == post_id))

    avg, cnt = q.one()
    return {"post_id": post_id, "average": float(avg) if avg is not None else 0.0, "count": int(cnt)}


async def get_comment_rating_summary(db: AsyncSession, comment_id: int) -> dict:
    q = await db.execute(func.avg(Rating.score), func.count(Rating.id).where(Rating.comment_id == comment_id))

    avg, cnt = q.one()
    return {"post_id": post_id, "average": float(avg) if avg is not None else 0.0, "count": int(cnt)}
