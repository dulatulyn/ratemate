from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi.security import HTTPBearer


from ratemate_app.db.session import get_db
from ratemate_app.schemas.comment import CommentCreate, CommentRead, RatingRequest, RatingResponse
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
    payload: CommentCreate,
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
    
    post = await db.get(Post, payload.post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    

    try:
        comment = await create_comment(db, user.id, payload)
    
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid parent_id")
    return comment

@router.get("/by_post/{post_id}", response_model=list[CommentRead])
async def get_comments_for_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    return await list_post_comments(db, post_id, limit, offset)

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

@router.get("/{comment_id}/rating", response_model=dict, summary="Get comment rating summary")
async def get_comment_rating(comment_id: int, db: AsyncSession = Depends(get_db)):
    summary = await get_comment_rating_summary(db, comment_id)
    return summary