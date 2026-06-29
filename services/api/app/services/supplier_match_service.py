"""
Supplier Match Service — Auto-match qualified suppliers based on categories.
"""
from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Supplier, SupplierCategory


async def match_suppliers(
    db: AsyncSession,
    category_ids: List[int],
    qualification_status: str = "QUALIFIED",
    limit: int = 20,
) -> Sequence[Supplier]:
    """Find qualified suppliers that match the given category IDs."""
    query = (
        select(Supplier)
        .options(selectinload(Supplier.categories))
        .where(
            Supplier.categories.any(SupplierCategory.id.in_(category_ids)),
            Supplier.qualification_status.in_([qualification_status, "QUALIFIED"]),
        )
        .order_by(Supplier.is_preferred.desc(), Supplier.evaluation_score.desc().nullslast())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.unique().scalars().all()
