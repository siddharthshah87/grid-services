from logging.config import fileConfig
import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
from app.models import Base

import os
import sys, pathlib

# Ensure the "app" package is importable when running Alembic directly
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from sqlmodel import SQLModel
import app.models  # Import models to ensure they are registered with SQLModel
from app.db.database import engine

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        context.configure(connection=conn, target_metadata=target_metadata)
        await context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
