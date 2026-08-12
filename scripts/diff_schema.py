"""Dry-run: compare SQLAlchemy models vs actual Postgres schema (async-safe).
Prints the ALTER/CREATE statements needed to sync the DB to the models.
Read-only: does NOT execute anything.
"""
import asyncio
import app.models.user, app.models.project, app.models.task, app.models.report
import app.models.brokerage, app.models.spare_part, app.models.quick_save
import app.models.knowledge, app.models.customer, app.models.file, app.models.logistics
from app.db import engine, Base
from sqlalchemy import MetaData
from sqlalchemy.dialects import postgresql


def pg_type(col):
    return col.type.compile(dialect=postgresql.dialect())


async def main():
    reflected = MetaData()
    async with engine.connect() as conn:
        await conn.run_sync(reflected.reflect)

    existing = set(reflected.tables.keys())
    md = Base.metadata

    print("=== MISSING TABLES (will be CREATE TABLE) ===")
    for tname, table in md.tables.items():
        if tname not in existing:
            print(f"  CREATE TABLE {tname}")

    print("=== MISSING COLUMNS (will be ALTER TABLE ADD COLUMN) ===")
    for tname, table in md.tables.items():
        if tname not in existing:
            continue
        db_cols = {c.name for c in reflected.tables[tname].columns}
        for col in table.columns:
            if col.name not in db_cols:
                nn = "NOT NULL" if not col.nullable else ""
                has_default = " (has default)" if col.default is not None else ""
                print(f"  ALTER TABLE {tname} ADD COLUMN {col.name} {pg_type(col)} {nn}{has_default}")


asyncio.run(main())
