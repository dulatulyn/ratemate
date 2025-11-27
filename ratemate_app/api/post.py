from fastapi import APIRouter, Depends, Header, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi.security import HTTPBearer

from ratemate_app.db.session import get_db
from ratemate_app.schemas.post import PostCreate, PostRead
from ratemate_app.schemas.comment import RatingRequest, RatingResponse
from ratemate_app.schemas.media import MediaRead
from ratemate_app.auth.security import decode_access_token
from ratemate_app.services.user import UserService
from ratemate_app.services.post import create_post
from ratemate_app.models.post import Post

router = APIRouter()

security = HTTPBearer()

@router.post("/", response_model=PostRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(security)])
async def create_post_endpoint(
    payload: PostCreate,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
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
    
    post = await create_post(db, owner_id=user.id, data=payload)

    return post
        

@router.post("/{post_id}/rate",
             status_code=status.HTTP_201_CREATED,
             response_model=RatingResponse,
             dependencies=[Depends(security)])
async def rate_post(post_id: int, rating: RatingRequest, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
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

    existing_post = await db.get(Post, post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    from ratemate_app.services.ratings import set_post_rating

    await set_post_rating(db, user.id, post_id, rating.score)

    return {"success": True}


@router.get("/{post_id}", response_model=PostRead)
async def get_post(post_id: int, include_media: bool = Query(True), db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    if include_media:
        return PostRead.model_validate({
            "id": post.id,
            "owner_id": post.owner_id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "media": media_reads,
            "media_urls": [mr.url for mr in media_reads]
        })
    else:
        return PostRead.model_validate({
            "id": post.id,
            "owner_id": post.owner_id,
            "title": post.title,
            "content": post.content,
            "created_at": post.created_at,
            "media": [],
            "media_urls": []
        })

@router.get("/{post_id}/rating")
async def get_post_rating(post_id: int, db: AsyncSession = Depends(get_db)):
    from ratemate_app.services.ratings import get_post_rating_summary

    summary = await get_post_rating_summary(db, post_id)

    return summary


@router.delete("/{post_id}/rating", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security)])
async def delete_post_rating_endpoint(post_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
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

    existing_post = await db.get(Post, post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    from ratemate_app.services.ratings import delete_post_rating
    await delete_post_rating(db, user.id, post_id)
    return


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security)])
async def delete_post_endpoint(post_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
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

    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")
    
    from ratemate_app.services.post import delete_post
    await delete_post(db, post)
    return
        