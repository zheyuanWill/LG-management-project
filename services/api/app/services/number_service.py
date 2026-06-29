"""
Number Generation Service

Handles business number generation with the ISO 9001 coding rules:
- Inquiry: RFQ-{project_code}{year}{seq}{batch}  e.g. RFQ-MT26001A
- Quote: QT-{project_code}{year}{seq}{batch}  e.g. QT-MT26001A
- Project: {company}-{project_code}{year}{seq}{category}  e.g. L-MT26001F
"""
import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iso_process import NumberSequence
from app.models.order import ProjectType


PROJECT_TYPE_CODE = {
    ProjectType.TECHNICAL_SERVICE: "MT",
    ProjectType.SUPERVISION: "SV",
    ProjectType.SPARE_PARTS: "SP",
    ProjectType.IMPORT_EXPORT_AGENT: "IE",
    ProjectType.BROKERAGE: "BK",
    ProjectType.AGENCY_FEE: "AG",
}

PROJECT_CATEGORY_CODE = {
    ProjectType.TECHNICAL_SERVICE: "R",
    ProjectType.SUPERVISION: "S",
    ProjectType.SPARE_PARTS: "P",
    ProjectType.IMPORT_EXPORT_AGENT: "T",
    ProjectType.BROKERAGE: "A",
    ProjectType.AGENCY_FEE: "A",
}

COMPANY_PREFIX = "L"


async def _next_seq(db: AsyncSession, prefix: str) -> int:
    result = await db.execute(
        select(NumberSequence).where(NumberSequence.prefix == prefix).with_for_update()
    )
    seq = result.scalar_one_or_none()
    if seq is None:
        seq = NumberSequence(prefix=prefix, current_value=1)
        db.add(seq)
        await db.flush()
        return 1
    seq.current_value += 1
    await db.flush()
    return seq.current_value


def _year_suffix() -> str:
    return datetime.date.today().strftime("%y")


async def generate_inquiry_no(db: AsyncSession, project_type: ProjectType, batch: str = "A") -> str:
    code = PROJECT_TYPE_CODE.get(project_type, "XX")
    year = _year_suffix()
    prefix = f"RFQ-{code}{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}{batch}"


async def generate_quote_no(db: AsyncSession, project_type: ProjectType, batch: str = "A") -> str:
    code = PROJECT_TYPE_CODE.get(project_type, "XX")
    year = _year_suffix()
    prefix = f"QT-{code}{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}{batch}"


async def generate_project_code(db: AsyncSession, project_type: ProjectType) -> str:
    code = PROJECT_TYPE_CODE.get(project_type, "XX")
    cat = PROJECT_CATEGORY_CODE.get(project_type, "X")
    year = _year_suffix()
    prefix = f"{COMPANY_PREFIX}-{code}{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}{cat}"


async def generate_change_no(db: AsyncSession) -> str:
    year = _year_suffix()
    prefix = f"CHG-{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}"


async def generate_acceptance_no(db: AsyncSession) -> str:
    year = _year_suffix()
    prefix = f"ACC-{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}"


async def generate_closure_no(db: AsyncSession) -> str:
    year = _year_suffix()
    prefix = f"CLS-{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}"


async def generate_complaint_no(db: AsyncSession) -> str:
    year = _year_suffix()
    prefix = f"CMP-{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}"


async def generate_survey_no(db: AsyncSession) -> str:
    year = _year_suffix()
    prefix = f"SVY-{year}"
    seq = await _next_seq(db, prefix)
    return f"{prefix}{seq:03d}"


def increment_batch(current_batch: str) -> str:
    """Increment batch letter: A->B, B->C, ..., Z->AA"""
    if not current_batch:
        return "B"
    last = current_batch[-1]
    if last == "Z":
        return current_batch + "A"
    return current_batch[:-1] + chr(ord(last) + 1)
