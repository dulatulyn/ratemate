from fastapi import FastAPI
from fastapi.security import HTTPBearer
import uvicorn
import logging
import asyncio

from ratemate_app.api.auth import router as auth_router
from ratemate_app.api.post import router as posts_router
from ratemate_app.api.comment import router as comments_router
from ratemate_app.api.follow import router as follows_router
from ratemate_app.api.chat import router as chats_router
from ratemate_app.api.admin import router as admin_router
from ratemate_app.api.lowkey import router as lowkeys_router

from ratemate_app.db.session import init_db, AsyncSessionLocal
from ratemate_app.db.base import import_models

from ratemate_app.services.lowkey import run_lowkey_expirer

import_models()

app = FastAPI(
    title="RateMate",
    version="1.0.0"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def on_startup():
    await init_db()
    app.state.lowkey_task = asyncio.create_task(run_lowkey_expirer(AsyncSessionLocal))

@app.get("/")
def root():
    return {"success": True}

@app.on_event("shutdown")
async def on_shutdown():
    task = getattr(app.state, "lowkey_task", None)
    if task:
        task.cancel()

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(posts_router, prefix="/posts", tags=["Posts"])
app.include_router(comments_router, prefix="/comments", tags=["Comments"])
app.include_router(follows_router, prefix="/follows", tags=["Follows"])
app.include_router(chats_router, prefix="/chats", tags=["Chats"])
app.include_router(admin_router, prefix="/lowkeys", tags=["Lowkeys"])
app.include_router(admin_router, prefix="/admin", tags=["Admin"])

from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run("ratemate_app.main:app", host="127.0.0.1", port=8080, reload=True)