from fastapi import APIRouter, Depends, Header, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Set

from ratemate_app.db.session import get_db, AsyncSessionLocal
from ratemate_app.auth.security import decode_access_token
from ratemate_app.services.user import UserService
from ratemate_app.services.chat import get_or_create_chat, send_message, list_recent_messages
from ratemate_app.schemas.chat import ChatRead, ChatCreate, MessageCreate, MessageRead
from ratemate_app.models.user import User
from ratemate_app.models.chat import Chat

router = APIRouter()
security = HTTPBearer()
_chat_conns: Dict[int, set[WebSocket]] = {}

@router.post("/with/{user_id}", response_model=ChatRead, dependencies=[Depends(security)], status_code=status.HTTP_201_CREATED)
async def start_or_get_chat(user_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    me = await UserService.get_user_by_username(db, username)
    if not me:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if me.id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid target")
    
    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    
    try:
        chat = await get_or_create_chat(db, me.id, user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pair")
    
    return chat


@router.post("/{chat_id}/messages", response_model=MessageRead, dependencies=[Depends(security)], status_code=status.HTTP_201_CREATED)
async def send_chat_message(chat_id: int, payload: MessageCreate, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        jwt = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = jwt.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    if user.id != chat.user1_id and user.id != chat.user2_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")
    
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Content must not be empty")
    
    msg = await send_message(db, chat_id, user.id, payload.content)

    conns = _chat_conns.get(chat_id, set())
    data = {"id": msg.id, "chat_id": msg.chat_id, "sender_id": msg.sender_id, "content": msg.content, "created_at": msg.created_at.isoformat()}

    for ws in list(conns):
        try:
            await ws.send_json(data)
        except:
            conns.discard(ws)

    return msg


@router.get("/{chat_id}/messages", response_model=list[MessageRead], dependencies=[Depends(security)])
async def get_recent_chat_messages(chat_id: int, authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authorization.split(" ", 1)[1]
    try:
        jwt = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
    
    username = jwt.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = await UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    if user.id != chat.user1_id and user.id != chat.user2_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant")
    
    msgs = await list_recent_messages(db, chat_id, limit, offset)

    return msgs


@router.websocket("/ws/{chat_id}")
async def websocket_chat(chat_id: int, websocket: WebSocket, token: str):
    try:
        payload = decode_access_token(token)
    except Exception:
        await websocket.close(code=4401)
        return
    
    await websocket.accept()
    async with AsyncSessionLocal() as db:
        username = payload.get("sub")
        if not username:
            await websocket.close(code=4401)
        
        user = await UserService.get_user_by_username(db, username)
        if not user:
            await websocket.close(code=4403)
            return

        chat = await db.get(Chat, chat_id)
        if not chat or (user.id != chat.user1_id and user.id != chat.user2_id):
            await websocket.close(code=4403)
            return
        
        conns = _chat_conns.setdefault(chat_id, set())
        conns.add(websocket)
        try:
            while True:
                incoming = await websocket.receive_json()
                content = incoming.get("content")
                if not isinstance(content, str) or not content.strip():
                    continue

                msg = await send_message(db, chat_id, user.id, content)
                data ={"id": msg.id, "chat_id": msg.chat_id, "sender_id": msg.sender_id, "content": msg.content, "created_at": msg.created_at.isoformat()}
                
                for ws in list(conns):
                    try:
                        await ws.send_json(data)
                    except:
                        conns.discard(ws)
        except WebSocketDisconnect:
            pass
        finally:
            conns.discard(websocket)

