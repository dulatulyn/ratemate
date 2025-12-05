from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ratemate_app.models.chat import Chat
from ratemate_app.models.message import Message

async def get_or_create_chat(db: AsyncSession, user1_id: int, user2_id: int) -> Chat:
    if user1_id == user2_id:
        raise ValueError("invalid_pair")
    
    a = min(user1_id, user2_id)
    b = max(user1_id, user2_id)
    
    q = await db.execute(
        select(Chat)
        .where(Chat.user1_id == a, Chat.user2_id == b)
    )

    row = q.scalar_one_or_none()
    if row:
        return row
    
    chat = Chat(user1_id=a, user2_id=b)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat

async def send_message(db: AsyncSession, chat_id: int, sender_id: int, content: str) -> Message:
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise ValueError("invalid_chat")
    if sender_id != chat.user1_id and sender_id != chat.user2_id:
        raise ValueError("not_member")
    
    msg = Message(chat_id=chat_id, sender_id=sender_id, content=content.strip())
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def list_recent_messages(db: AsyncSession, chat_id: int, limit: int = 50, offset: int = 0) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return result.scalars().all()

async def redact_message_content(db: AsyncSession, message_id: int, requester_id: int) -> Message:
    msg = await db.get(Message, message_id)
    if not msg:
        raise ValueError("not_found")
    if msg.sender_id != requester_id:
        raise ValueError("forbidden")
    msg.content = ""
    
    await db.commit()
    await db.refresh(msg)
    return msg