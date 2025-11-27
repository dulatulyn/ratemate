from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ratemate_app.core.config import settings
from ratemate_app.schemas.token import Token
from ratemate_app.db.session import get_db
from ratemate_app.schemas.user import UserLogin, UserCreate
from ratemate_app.services.user import UserService
from ratemate_app.auth.security import create_access_token, decode_access_token
from datetime import timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_tokens(
    user_login: UserLogin,
    db: AsyncSession = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    logger.info(f"Login attempt for user: {user_login.username}")

    user = await UserService.authenticate_user(
        db, user_login.username, user_login.password
    )
    if not user:
        logger.warning(f"Failed login attempt for user {user_login.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta = access_token_expires
    )

    logger.info(f"Successful login for user: {user.username}")

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
    
    
@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Registration attempt for user: {user.username}")

    db_user = await UserService.get_user_by_username(db, user.username)
    if db_user:
        logger.warning(f"Registration attempt with existing username: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    db_user = await UserService.get_user_by_email(db, email=user.email)

    if db_user:
        logger.warning(f"Registration attempt with existing email: {user.email}")
        raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    new_user = await UserService.create_user(db=db, user_create=user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": new_user.username},
        expires_delta=access_token_expires
    )

    logger.info(f"Successful registration for user: {user.username}")
    return {"access_token": access_token,
            "token_type": "bearer"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security)])
async def delete_me(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
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
    
    await UserService.delete_user(db, user)
    return
