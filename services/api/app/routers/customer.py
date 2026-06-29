"""Customer Router"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundError, ConflictError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.models.user import User
from app.models.customer import Customer, Vessel
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerResponse, CustomerWithVessels,
    VesselCreate, VesselUpdate, VesselResponse
)
from app.schemas.common import PageResponse

router = APIRouter(prefix="/customers", tags=["客户管理"])


@router.get("", response_model=PageResponse[CustomerResponse])
async def list_customers(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.READ))
):
    """获取客户列表"""
    query = select(Customer)
    if keyword:
        query = query.where(
            Customer.name.ilike(f"%{keyword}%") | 
            Customer.code.ilike(f"%{keyword}%")
        )
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PageResponse.create(items=items, total=total, page=page, size=size)


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.CREATE))
):
    """创建客户"""
    # Check code unique
    existing = await db.execute(select(Customer).where(Customer.code == data.code))
    if existing.scalar_one_or_none():
        raise ConflictError("客户编码已存在")
    
    customer = Customer(**data.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerWithVessels)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.READ))
):
    """获取客户详情"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户", customer_id)
    
    # Get vessels
    vessels_result = await db.execute(
        select(Vessel).where(Vessel.customer_id == customer_id)
    )
    vessels = vessels_result.scalars().all()
    
    return CustomerWithVessels.model_validate({
        "id": customer.id,
        "name": customer.name,
        "code": customer.code,
        "contact_person": customer.contact_person,
        "contact_phone": customer.contact_phone,
        "contact_email": customer.contact_email,
        "address": customer.address,
        "notes": customer.notes,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
        "vessels": [VesselResponse.model_validate(v) for v in vessels]
    })


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.UPDATE))
):
    """更新客户"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户", customer_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    
    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.DELETE))
):
    """删除客户"""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise NotFoundError("客户", customer_id)
    
    await db.delete(customer)
    await db.commit()
    return {"message": "删除成功"}


# Vessel routes
@router.get("/{customer_id}/vessels", response_model=List[VesselResponse])
async def list_customer_vessels(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.READ))
):
    """获取客户船舶列表"""
    result = await db.execute(
        select(Vessel).where(Vessel.customer_id == customer_id)
    )
    return result.scalars().all()


@router.post("/vessels", response_model=VesselResponse)
async def create_vessel(
    data: VesselCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.CREATE))
):
    """创建船舶"""
    # Check customer exists
    customer = await db.execute(select(Customer).where(Customer.id == data.customer_id))
    if not customer.scalar_one_or_none():
        raise NotFoundError("客户", data.customer_id)
    
    vessel = Vessel(**data.model_dump())
    db.add(vessel)
    await db.commit()
    await db.refresh(vessel)
    return vessel


@router.put("/vessels/{vessel_id}", response_model=VesselResponse)
async def update_vessel(
    vessel_id: int,
    data: VesselUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.UPDATE))
):
    """更新船舶"""
    result = await db.execute(select(Vessel).where(Vessel.id == vessel_id))
    vessel = result.scalar_one_or_none()
    if not vessel:
        raise NotFoundError("船舶", vessel_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(vessel, key, value)
    
    await db.commit()
    await db.refresh(vessel)
    return vessel


@router.delete("/vessels/{vessel_id}")
async def delete_vessel(
    vessel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.ORDER, Action.DELETE))
):
    """删除船舶"""
    result = await db.execute(select(Vessel).where(Vessel.id == vessel_id))
    vessel = result.scalar_one_or_none()
    if not vessel:
        raise NotFoundError("船舶", vessel_id)
    
    await db.delete(vessel)
    await db.commit()
    return {"message": "删除成功"}

