"""
Base Service with common CRUD operations.

All domain services inherit from this to get pagination,
get-by-id, and other common patterns for free.
"""
from typing import TypeVar, Generic, Type, Optional, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.core.exceptions import NotFoundError

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """
    Generic base service providing common CRUD operations.

    Usage:
        class OrderService(BaseService[Order]):
            def __init__(self):
                super().__init__(Order)
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(
        self,
        db: AsyncSession,
        id: int,
        *,
        raise_not_found: bool = True,
    ) -> Optional[ModelType]:
        """Get a single record by ID."""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        instance = result.scalar_one_or_none()
        if instance is None and raise_not_found:
            raise NotFoundError(self.model.__tablename__, id)
        return instance

    async def list_paginated(
        self,
        db: AsyncSession,
        *,
        query=None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[ModelType], int]:
        """List records with pagination. Returns (items, total)."""
        if query is None:
            query = select(self.model)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        items = result.scalars().all()

        return items, total

    async def create(self, db: AsyncSession, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        db.add(instance)
        await db.flush()
        return instance

    async def update(
        self,
        db: AsyncSession,
        instance: ModelType,
        **kwargs,
    ) -> ModelType:
        """Update an existing record."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(instance, key, value)
        await db.flush()
        return instance

    async def delete(self, db: AsyncSession, instance: ModelType) -> None:
        """Delete a record."""
        await db.delete(instance)
        await db.flush()
