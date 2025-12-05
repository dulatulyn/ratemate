from fastapi import APIRouter, Depends, Header, HTTPException, status, UploadFile, File, Query
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import timedelta, datetime
from sqlalchemy import select

from ratemate_app.db.session import get_db
from ratemate_app.auth.security import decode_access_token
from ratemate_app.services.user import UserService
from ratemate_app.services.lowkey import create_lowkey, delete_lowkey, get_lowkey, list_public_active_lowkeys, list_following_active_lowkeys, mark_view, list_views
from ratemate_app.services.ratings import set_lowkey_rating, get_lowkey_rating_summary, delete_lowkey_rating
from ratemate_app.schemas.lowkey import LowkeyRead, LowkeyCreate, LowkeyViewRead
from ratemate_app.schemas.comment import RatingRequest
from ratemate_app.models.lowkey import Lowkey
from ratemate_app.models.follow import Follow

router = APIRouter()
security = HTTPBearer()

@router.post("/", response_model=LowkeyRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security)])
async def create_lowkey_endpoint(title: Optional[str] = None, visibility: Optional[str] = None, file: UploadFile = File(...), authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    row = await create_lowkey(db, user.id, title, file, visibility or 'public')
    expires_at = row.created_at + timedelta(hours=24)
    return LowkeyRead.model_validate({
        "id": row.id,
        "owner_id": row.owner_id,
        "title": row.title,
        "media_url": row.media_url,
        "media_type": row.media_type,
        "created_at": row.created_at,
        "expires_at": expires_at
    })


@router.get("/public", response_model=list[LowkeyRead], dependencies=[Depends(security)])
async def list_public_lowkeys(authorization: Optional[str] = Header(None), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    rows = await list_public_active_lowkeys(db, limit, offset)
    out: list[LowkeyRead] = []
    for row in rows:
        out.append(LowkeyRead.model_validate({
            "id": row.id,
            "owner_id": row.owner_id,
            "title": row.title,
            "media_url": row.media_url,
            "media_type": row.media_type,
            "created_at": row.created_at,
            "expires_at": row.created_at + timedelta(hours=24)
        }))
    return out


@router.get("/feed", response_model=list[LowkeyRead], dependencies=[Depends(security)])
async def list_feed_lowkeys(authorization: Optional[str] = Header(None), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    rows = await list_following_active_lowkeys(db, user.id, limit, offset)
    out: list[LowkeyRead] = []
    for row in rows:
        out.append(LowkeyRead.model_validate({
            "id": row.id,
            "owner_id": row.owner_id,
            "title": row.title,
            "media_url": row.media_url,
            "media_type": row.media_type,
            "created_at": row.created_at,
            "expires_at": row.created_at + timedelta(hours=24)
        }))
    return out

@router.get("/{lowkey_id}", response_model=LowkeyRead, dependencies=[Depends(security)])
async def get_lowkey_endpoint(lowkey_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    row = await get_lowkey(db, lowkey_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lowkey not found")
   
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    viewer = await UserService.get_user_by_username(db, username)
    if not viewer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if getattr(row, "visibility", None) == 'followers' and viewer.id != row.owner_id:
        exists = await db.execute(select(Follow).where(Follow.follower_id == viewer.id, Follow.followed_id == row.owner_id))
        if not exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not allowed")
    await mark_view(db, lowkey_id, viewer.id)

    return LowkeyRead.model_validate({
        "id": row.id,
        "owner_id": row.owner_id,
        "title": row.title,
        "media_url": row.media_url,
        "media_type": row.media_type,
        "created_at": row.created_at,
        "expires_at": row.created_at + timedelta(hours=24)
    })


@router.get("/{lowkey_id}/views", response_model=list[LowkeyViewRead])
async def list_lowkey_views_endpoint(lowkey_id: int, db: AsyncSession = Depends(get_db)):
    rows = await list_views(db, lowkey_id)
    return [LowkeyViewRead(viewer_id=vid, username=uname, viewed_at=vt) for (vid, uname, vt) in rows]


@router.post("/{lowkey_id}/rate", status_code=status.HTTP_201_CREATED, dependencies=[Depends(security)])
async def rate_lowkey(lowkey_id: int, payload: RatingRequest, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        jwt = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    username = jwt.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target = await get_lowkey(db, lowkey_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lowkey not found")
    
    if getattr(target, "visibility", None) == 'followers' and user.id != target.owner_id:
        exists = await db.execute(
            select(Follow)
            .where(Follow.follower_id == user.id, Follow.followed_id == target.owner_id)
        )
        if not exists.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not allowed")

    await set_lowkey_rating(db, user.id, lowkey_id, payload.score)

    return {"success": True}


@router.delete("/{lowkey_id}/rating", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security)])
async def delete_lowkey_rating_endpoint(lowkey_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload_jwt = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload_jwt.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target = await get_lowkey(db, lowkey_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lowkey not found")
    await delete_lowkey_rating(db, user.id, lowkey_id)

    return

@router.delete("/{lowkey_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security)])
async def delete_lowkey_endpoint(lowkey_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload_jwt = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload_jwt.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    row = await db.get(Lowkey, lowkey_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lowkey not found")
    if row.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")
    
    await delete_lowkey(db, row)
    return


