from fastapi import APIRouter, Depends, Header, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi.security import HTTPBearer

from ratemate_app.db.session import get_db
from ratemate_app.schemas.comment import CommentCreate, CommentRead, RatingRequest, RatingResponse
from ratemate_app.schemas.media import MediaRead
from ratemate_app.auth.security import decode_access_token
from ratemate_app.services.user import UserService
from ratemate_app.services.comment import create_comment, list_post_comments
from ratemate_app.services.ratings import set_comment_rating, get_comment_rating_summary
from ratemate_app.models.post import Post
from ratemate_app.models.comment import Comment


security = HTTPBearer()

router = APIRouter()

@router.post("/", response_model=CommentRead, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(security)])
async def create_comment_endpoint(
    payload: Optional[CommentCreate] = None,
    post_id: Optional[int] = Form(None),
    content: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    files: list[UploadFile] | None = File(None),
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
    
    data = payload if payload is not None else CommentCreate(post_id=post_id, content=content or "", parent_id=parent_id)
    if not data.content or not data.content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Content must not be empty")
    
    post = await db.get(Post, data.post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    try:
        comment = await create_comment(db, user.id, data)
    
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid parent_id")

    media_reads: list[MediaRead] = []
    if files:
        if len(files) > 5:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Too many files (max 5)")
        
        from ratemate_app.services.media import upload_comment_media_bulk, list_comment_media
        await upload_comment_media_bulk(db, comment.id, files)
        medias = await list_comment_media(db, comment.id)
        media_reads = [MediaRead.model_validate(m, from_attributes=True) for m in medias]

        return CommentRead.model_validate({
            "id": comment.id,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "parent_id": comment.parent_id,
            "media": media_reads,
            "media_urls": [mr.url for mr in media_reads]
        })
    

@router.get("/by_post/{post_id}", response_model=list[CommentRead])
async def get_comments_for_post(
    post_id: int,
    include_media: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    items = await list_post_comments(db, post_id, limit, offset)

    if not include_media:
        medias = await list_comment_media(db, comment.id)
        
        return [ CommentRead.model_validate({
                "id": comment.id,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "parent_id": comment.parent_id,
                "media": [],
                "media_urls": []
            }) for comment in items
        ]
    
    from ratemate_app.services.media import list_comment_media 
    result: list[CommentRead] = []

    for comment in items:
        medias = await list_comment_media(db, comment.id)
        media_reads = [MediaRead.model_validate(m, from_attributes=True) for m in medias]
        result.append(CommentRead.model_validate({
                "id": comment.id,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "content": comment.content,
                "created_at": comment.created_at,
                "parent_id": comment.parent_id,
                "media": media_reads,
                "media_urls": [mr.url for mr in media_reads]
            }))
    return result

@router.post("/{comment_id}/rate", 
             status_code=status.HTTP_201_CREATED, 
             response_model=RatingResponse,
             dependencies=[Depends(security)]
             )
async def rate_comment(
    comment_id: int,
    rating: RatingRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
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
    
    existing_comment = await db.get(Comment, comment_id)
    if not existing_comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    await set_comment_rating(db, user.id, comment_id, rating.score)
    return {"success": True}


@router.get("/{comment_id}", response_model=CommentRead)
async def get_comment(comment_id: int, include_media: bool = Query(True), db: AsyncSession = Depends(get_db)):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    
    if include_media:
        from ratemate_app.services.media import list_comment_media
        medias = await list_comment_media(db, comment_id)
        media_reads = [MediaRead.model_validate(m, from_attributes=True) for m in medias]

        return CommentRead.model_validate({
            "id": comment.id,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "parent_id": comment.parent_id,
            "media": media_reads,
            "media_urls": [mr.url for mr in media_reads]
        })

    else:
        return CommentRead.model_validate({
            "id": comment.id,
            "user_id": comment.user_id,
            "post_id": comment.post_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "parent_id": comment.parent_id,
            "media": [],
            "media_urls": []
        })


@router.post("/{comment_id}/media", response_model=list[MediaRead], status_code=status.HTTP_201_CREATED, dependencies=[Depends(security)])
async def upload_comment_media_endpoint(comment_id: int, files: list[UploadFile] | None = File(None), authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
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
    
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    
    if comment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the author")

    if files and len(files) > 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Too many files (max 5)")
    
    if files:
        from ratemate_app.services.media import upload_comment_media_bulk, list_comment_media
        await upload_comment_media_bulk(db, comment.id, files)
        medias = await list_comment_media(db, comment.id)
        return [MediaRead.model_validate(m, from_attributes=True) for m in medias]
    else:
        return []



@router.get("/{comment_id}/rating", response_model=dict, summary="Get comment rating summary")
async def get_comment_rating(comment_id: int, db: AsyncSession = Depends(get_db)):
    summary = await get_comment_rating_summary(db, comment_id)
    return summary


@router.delete("/{comment_id}/rating", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security)])
async def delete_comment_rating_endpoint(comment_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
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
    
    existing_comment = await db.get(Comment, comment_id)
    if not existing_comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    from ratemate_app.services.ratings import delete_comment_rating
    await delete_comment_rating(db, user.id, comment_id)
    return


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security)])
async def delete_comment_endpoint(comment_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
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
    
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the author")
    
    from ratemate_app.services.comment import delete_comment
    await delete_comment(db, comment)
    return