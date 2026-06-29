"""
Pre-migration startup script.

Completely bypasses Alembic migrations to avoid PostgreSQL enum-type
conflicts.  Strategy:

  1. Create all enum types idempotently (DO $$ … EXCEPTION).
  2. Create all tables via Base.metadata.create_all (checkfirst=True).
     Models all use create_type=False, so no CREATE TYPE is emitted.
  3. Stamp alembic_version to head so future migrations work.
"""
import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

ENUM_TYPES = {
    "userrole": ("OWNER", "PM", "PROC", "FIN", "OPS"),
    "suppliertype": ("GOODS", "SERVICE"),
    "currency": ("CNY", "USD", "EUR", "JPY", "HKD"),
    "projecttype": ("TECHNICAL_SERVICE", "SUPERVISION", "SPARE_PARTS",
                     "IMPORT_EXPORT_AGENT", "BROKERAGE", "AGENCY_FEE"),
    "orderstatus": ("INQUIRY", "DRAFT", "IN_PROGRESS", "COMPLETED", "CANCELLED"),
    "quotestatus": ("DRAFT", "SENT", "FEEDBACK", "ACCEPTED", "REJECTED"),
    "contractstatus": ("DRAFT", "PENDING_APPROVAL", "EFFECTIVE", "EXECUTING",
                        "COMPLETED", "TERMINATED"),
    "procurementstatus": ("DRAFT", "PENDING_APPROVAL", "APPROVED", "ORDERED",
                           "PARTIAL_RECEIVED", "RECEIVED", "CANCELLED"),
    "inventorymovementtype": ("IN", "OUT", "RESERVE", "RELEASE", "ADJUST"),
    "nodestatus": ("PENDING", "IN_PROGRESS", "COMPLETED", "OVERDUE", "SKIPPED"),
    "settlementstatus": ("DRAFT", "PENDING_APPROVAL", "APPROVING", "APPROVED",
                          "REJECTED", "COMPLETED"),
    "fileobjecttype": ("ORDER", "QUOTE", "CONTRACT", "PROCUREMENT",
                        "TRACKING_NODE", "SETTLEMENT", "INVOICE",
                        "BILL_OF_LADING", "ACCEPTANCE", "PHOTO",
                        "RISK_ASSESSMENT", "CONTRACT_REVIEW",
                        "QUALITY_INSPECTION", "PROJECT_CHANGE",
                        "PROJECT_CLOSURE", "COMPLAINT",
                        "SUPPLIER_ADMISSION", "KNOWLEDGE", "OTHER"),
    "risklevel": ("HIGH", "MEDIUM", "LOW"),
    "approvalstatus": ("PENDING", "APPROVED", "REJECTED"),
    "inquirymethod": ("EMAIL", "PHONE", "CHAT"),
    "inspectionresult": ("PASS", "FAIL", "CONDITIONAL"),
    "complaintstatus": ("RECEIVED", "INVESTIGATING", "RESOLVED", "CLOSED"),
    "surveystatus": ("DRAFT", "SENT", "RESPONDED", "CLOSED"),
    "evaluationlevel": ("EXCELLENT", "QUALIFIED", "OBSERVED", "ELIMINATED"),
    "changetype": ("REQUIREMENT", "PRICE", "SCHEDULE", "SCOPE"),
    "closurestatus": ("DRAFT", "PENDING", "APPROVED", "CLOSED"),
    "workflowstatus": ("PENDING", "APPROVED", "REJECTED", "CANCELLED"),
    "workflownodestatus": ("PENDING", "APPROVED", "REJECTED"),
    "syncdirection": ("LG_TO_JDY", "JDY_TO_LG"),
    "syncstatus": ("PENDING", "SUCCESS", "FAILED"),
    "notificationtype": ("INFO", "WARNING", "ERROR", "SUCCESS"),
}

ALEMBIC_HEAD = "002_iso9001"


async def ensure_enum_types(conn) -> None:
    for name, values in ENUM_TYPES.items():
        values_sql = ", ".join(f"'{v}'" for v in values)
        await conn.execute(text(
            f"DO $$ BEGIN "
            f"CREATE TYPE {name} AS ENUM ({values_sql}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; "
            f"END $$;"
        ))
    print(f"pre_migrate: {len(ENUM_TYPES)} enum types ensured.")


async def create_tables(conn) -> None:
    from app.db.base import Base  # noqa
    import app.models  # noqa – registers all models with Base.metadata

    await conn.run_sync(Base.metadata.create_all)
    print("pre_migrate: all tables ensured via create_all.")


async def stamp_alembic(conn) -> None:
    await conn.execute(text(
        "CREATE TABLE IF NOT EXISTS alembic_version ("
        "version_num VARCHAR(32) NOT NULL, "
        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
    ))
    await conn.execute(text("DELETE FROM alembic_version"))
    await conn.execute(text(
        f"INSERT INTO alembic_version (version_num) VALUES ('{ALEMBIC_HEAD}')"
    ))
    print(f"pre_migrate: stamped alembic_version = {ALEMBIC_HEAD}")


async def run() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("DATABASE_URL not set – skipping pre-migration")
        return

    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            await ensure_enum_types(conn)
            await create_tables(conn)
            await stamp_alembic(conn)
        print("pre_migrate: done")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as exc:
        print(f"pre_migrate FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
