from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from ratemate_app.core.config import settings
from sqlalchemy import text

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    from ratemate_app.db.base import Base, import_models
    import_models()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS title VARCHAR NULL"))
        await conn.execute(text("ALTER TABLE ratings ADD COLUMN IF NOT EXISTS comment_id INTEGER NULL"))
        await conn.execute(text("ALTER TABLE comments ADD COLUMN IF NOT EXISTS parent_id INTEGER NULL"))

async def close_db():
    await engine.dispose()