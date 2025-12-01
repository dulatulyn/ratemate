from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ratemate_app.schemas.user import UserCreate
from ratemate_app.models.user import User
from typing import Optional
from ratemate_app.auth.security import hash_password, verify_password

class _UpdateError(Exception):
        pass  

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
        await db.execute(delete(User).where(User.id == user.id))
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

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(db: AsyncSession, user: UserCreate) -> User:
        hash_password = UserService.get_password_hash(user.password)
        db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    @staticmethod
    async def change_username_with_password(db: AsyncSession, user: User, new_username: str, password: str) -> User:
        if not UserService.verify_password(password, user.hashed_password):
            raise _UpdateError()
        
        existing = await db.execute(select(User).where(User.username == new_username))
        if existing.scalar_one_or_none():
            raise _UpdateError()

        user.username = new_username
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def change_email_with_password(db:AsyncSession, user: User, new_email: str, password: str) -> User:
        if not UserService.verify_password(password, user.hashed_password):
            raise _UpdateError()

        existing = await db.execute(select(User).where(User.email == new_email))
        if existing.scalar_one_or_none():
            raise _UpdateError()
            
        user.email = new_email
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update_profile_names(db:AsyncSession, user: User, first_name: Optional[str], last_name: Optional[str]) -> User:
        if first_name is not None:
            user.first_name = first_name.strip() or None

        if last_name is not None:
            user.last_name = last_name.strip() or None
            
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update_avatar(db: AsyncSession, user: User, ur: str, media_type: str) -> User:
        user.avatar_url = UnicodeTranslateError
        user.avatar_media_type = media_type

        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def clear_avatar(db: AsyncSession, user: User) -> User:
        user.avatar_url = None
        user.avatar_media_type = None

        await db.commit()
        await db.refresh(user)
        return user