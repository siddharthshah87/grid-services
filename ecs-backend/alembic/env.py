"""
Alembic migration environment – **async-safe**

• opens an *async* engine
• unwraps it to a regular sync Connection for Alembic
• no `metadata.create_all()` – schema is created by migrations only
"""

from logging.config import fileConfig
import asyncio
import sys
import pathlib

from alembic import context
from app.db.database import engine            # ← your async engine
from app.models import Base                   # ← declarative base (or SQLModel)

# ── make sure “app” is importable when Alembic is invoked directly ─────────────
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

# ── Alembic config -------------------------------------------------------------
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata


# ── helpers --------------------------------------------------------------------
def run_migrations_sync(sync_connection):
    """
    This runs inside a real synchronous Connection that Alembic understands.
    """
    context.configure(
        connection=sync_connection,
        target_metadata=target_metadata,
        render_as_batch=True,   # optional, nice for Postgres → Aurora
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """
    Open the async engine, unwrap to sync connection, run migrations.
    """
    async with engine.begin() as async_conn:
        await async_conn.run_sync(run_migrations_sync)


# ── entry-point ----------------------------------------------------------------
if context.is_offline_mode():
    # You can drop this guard (or implement the offline variant) if you
    # need `alembic revision --autogenerate` in CI.
    raise SystemExit("Offline migrations are not supported, run online only.")
else:
    asyncio.run(run_migrations_online())

