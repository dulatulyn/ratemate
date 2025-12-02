from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, text, text as _text
from fastapi import UploadFile
from datetime import datetime, timedelta

import asyncio

from ratemate_app.models.lowkey import Lowkey, LowkeyView
from ratemate_app.models.follow import Follow
from ratemate_app.models.user import User

async def create_lowkey(db: AsyncSession, owner_id: int, title: str | None, file: UploadFile, visibility: str | None = 'public') -> Lowkey:
    row = Lowkey(owner_id=owner_id, title=title, visibility=visibility or 'public')
    db.add(row)
    await db.commit()
    await db.refresh(row)

    from ratemate_app.services.media import upload_lowkey_media
    url, media_type = await upload_lowkey_media(row.id, file)

    row.media_url = url
    row.media_type = media_type
    
    await db.commit()
    await db.refresh(row)
    return row

async def delete_lowkey(db: AsyncSession, lowkey: Lowkey) -> None:
    from ratemate_app.services.media import delete_lowkey_media_blob

    if lowkey.media_url:
        await delete_lowkey_media_blob(lowkey.media_url)
    await db.execute(delete(Lowkey).where(Lowkey.id == lowkey.id))
    await db.commit()

async def get_lowkey(db: AsyncSession, lowkey_id: int) -> Lowkey | None:
    q = await db.execute(select(Lowkey).where(Lowkey.id == lowkey_id, Lowkey.is_active == True))
    return q.scalar_one_or_none()

async def mark_view(db: AsyncSession, lowkey_id: int, viewer_id: int) -> None:
    existing = await db.execute(select(LowkeyView).where(LowkeyView.lowkey_id == lowkey_id, LowkeyView.viewer_id == viewer_id))
    if existing.scalar_one_or_none():
        return

    v = LowkeyView(lowkey_id=lowkey_id, viewer_id=viewer_id)
    db.add(v)
    await db.commit()

async def list_public_active_lowkeys(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[Lowkey]:
    q = await db.execute(
        select(Lowkey)
        .where(Lowkey.is_active == True)
        .where(Lowkey.visibility == 'public')
        .order_by(Lowkey.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return q.scalars().all()

async def list_following_active_lowkeys(db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0) -> list[Lowkey]:
    q = await db.execute(select(Lowkey)
                         .join(Follow, Follow.followed_id == Lowkey.owner_id)
                         .where(Follow.follower_id == user_id)
                         .where(Lowkey.is_active == True)
                         .order_by(Lowkey.created_at.desc())
                         .limit(limit)
                         .offset(offset))

    return q.scalars().all()

async def list_views(db: AsyncSession, lowkey_id: int) -> list[tuple[int, str, datetime]]:
    q = await db.execute(select(LowkeyView.viewer_id, User.username, LowkeyView.viewed_at)
                         .join(User, User.id == LowkeyView.viewer_id)
                         .where(LowkeyView.lowkey_id == lowkey_id)
                         .order_by(LowkeyView.viewed_at.desc()))
    return q.all()

async def expire_lowkeys(db: AsyncSession) -> None:
    await db.execute(_text("UPDATE lowkeys SET is_active = FALSE WHERE is_active = TRUE AND created_at < now() - interval '24 hours'"))
    await db.commit()

async def run_lowkey_expirer(session_factory) -> None:
    while True:
        try:
            async with session_factory() as db:
                await expire_lowkeys(db)
        except Exception:
            pass
        await asyncio.sleep(300)