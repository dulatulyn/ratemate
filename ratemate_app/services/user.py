from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ratemate_app.schemas.user import UserCreate
from ratemate_app.models.user import User
from typing import Optional
from ratemate_app.auth.security import hash_password, verify_password

class UserService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return hash_password(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    @staticmethod
    async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
        hashed_password = UserService.get_password_hash(user_create.password)
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def delete_user(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.commit()

    @staticmethod
    async def authenticate_user(db: AsyncSession, username_or_email: str, password: str) -> Optional[User]:
        user = await UserService.get_user_by_username_or_email(db, username_or_email)
        if not user:
            return None
        if not user.is_active:
            return None
        if not UserService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    async def get_user_by_username_or_email(db: AsyncSession, identifier: str) -> Optional[User]:
        user = await UserService.get_user_by_username(db, identifier)
        if user:
            return user
        
        user = await UserService.get_user_by_email(db, identifier)
        return user
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
async def get_user_by_email(db: AsyncSession, email: str):
    return await UserService.get_user_by_email(db, email)

async def create_user(db: AsyncSession, user: UserCreate):
    return await UserService.create_user(db, user)