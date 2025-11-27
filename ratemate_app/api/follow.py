from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ratemate_app.db.session import get_db
from ratemate_app.auth.security import decode_access_token
from ratemate_app.services.user import UserService
from ratemate_app.services.follow import follow_user, unfollow_user, list_following, list_followers, list_common_following
from ratemate_app.schemas.user import UserSummary
from ratemate_app.models.user import User

router = APIRouter()

security = HTTPBearer()

@router.post("/{user_id}", status_code=status.HTTP_201_CREATED, dependencies=[Depends(security)])
async def follow(user_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token Payload")
        
    me = await UserService.get_user_by_username(db, username)
    if not me:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    if me.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow self")
    try:
        await follow_user(db, me.id, user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow self")
    
    return {"success": True}


@router.delete("/{user_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(security)])
async def unfollow(user_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token Payload")
        
    me = await UserService.get_user_by_username(db, username)
    if not me:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    await unfollow_user(db, me.id, user_id)

    return {"success": True}


@router.get("/me/following", response_model=list[UserSummary], dependencies=[Depends(security)])
async def get_my_following(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token Payload")
        
    me = await UserService.get_user_by_username(db, username)
    if not me:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    users = await list_following(db, me.id)
    return users


@router.get("/me/followers", response_model=list[UserSummary], dependencies=[Depends(security)])
async def get_my_followers(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token Payload")
        
    me = await UserService.get_user_by_username(db, username)
    if not me:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    users = await list_followers(db, me.id)
    return users


@router.get("/common_with/{user_id}", response_model=list[UserSummary], dependencies=[Depends(security)])
async def get_common_following(user_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token Payload")
        
    me = await UserService.get_user_by_username(db, username)
    if not me:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    users = await list_common_following(db, me.id, user_id)
    return users