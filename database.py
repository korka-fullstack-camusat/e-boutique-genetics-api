import os
import re
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

_raw = os.getenv("DATABASE_URL", "")
_base = re.sub(r"\?.*$", "", _raw)  # strip existing query params

# psycopg3 — pure Python, no compilation, Python 3.14 compatible.
# Same URL (postgresql+psycopg://) works for both:
#   - create_async_engine  (app)
#   - engine_from_config   (Alembic migrations, sync)
DATABASE_URL = (
    _base.replace("postgresql://", "postgresql+psycopg://", 1)
    + "?sslmode=require"
)

engine = create_async_engine(
    DATABASE_URL,
    # Neon pgbouncer handles connection pooling at the proxy level.
    # Keep per-worker pool small to avoid exhausting the 100-conn limit.
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
