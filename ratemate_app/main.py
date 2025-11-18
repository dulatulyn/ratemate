from fastapi import FastAPI
import uvicorn
import logging
from ratemate_app.api.auth import router as auth_router
from ratemate_app.api.post import router as posts_router
from ratemate_app.api.comment import router as comments_router

from ratemate_app.db.session import init_db

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
def root():
    return {"success": True}

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(posts_router, prefix="/posts", tags=["Posts"])
app.include_router(comments_router, prefix="/comments", tags=["Comments"])

if __name__ == "__main__":
    uvicorn.run("ratemate_app.main:app", host="127.0.0.1", port=8080, reload=True)