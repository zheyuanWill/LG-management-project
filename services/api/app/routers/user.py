"""User Management Router"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.exceptions import NotFoundError, ForbiddenError, ConflictError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.common import PageResponse

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("", response_model=PageResponse[UserResponse])
async def list_users(
    keyword: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.READ))
):
    """获取用户列表 - 仅OWNER角色可访问"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限访问")
    
    query = select(User)
    
    if keyword:
        query = query.where(
            User.username.ilike(f"%{keyword}%") | 
            User.real_name.ilike(f"%{keyword}%") |
            User.email.ilike(f"%{keyword}%")
        )
    
    if role:
        query = query.where(User.role == role)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Paginate
    query = query.order_by(User.id).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PageResponse.create(items=items, total=total, page=page, size=size)


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.CREATE))
):
    """创建用户 - 仅OWNER角色可操作"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限操作")
    
    # Check username unique
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise ConflictError("用户名已存在")
    
    # Check email unique if provided
    if data.email:
        existing_email = await db.execute(select(User).where(User.email == data.email))
        if existing_email.scalar_one_or_none():
            raise ConflictError("邮箱已被使用")
    
    user = User(
        username=data.username,
        email=data.email,
        real_name=data.real_name,
        role=data.role,
        hashed_password=get_password_hash(data.password),
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.READ))
):
    """获取用户详情 - 仅OWNER角色可访问"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限访问")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.UPDATE))
):
    """更新用户 - 仅OWNER角色可操作"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限操作")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)
    
    # Filter out sensitive fields that should not be set directly
    PROTECTED_FIELDS = {"hashed_password", "is_active", "id", "created_at", "updated_at"}
    for key, value in data.model_dump(exclude_unset=True).items():
        if key not in PROTECTED_FIELDS:
            setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role: UserRole,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.UPDATE))
):
    """更改用户角色 - 仅OWNER角色可操作"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限操作")
    
    if user_id == current_user.id:
        raise ConflictError("不能修改自己的角色")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)
    
    user.role = role
    await db.commit()
    await db.refresh(user)
    return user


@router.put("/{user_id}/password")
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=6, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.UPDATE))
):
    """重置用户密码 - 仅OWNER角色可操作"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限操作")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)
    
    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    return {"message": "密码重置成功"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.DELETE))
):
    """删除用户（禁用） - 仅OWNER角色可操作"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限操作")
    
    if user_id == current_user.id:
        raise ConflictError("不能删除自己")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)
    
    # Soft delete - just deactivate
    user.is_active = False
    await db.commit()
    return {"message": "用户已禁用"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.USER, Action.UPDATE))
):
    """启用用户 - 仅OWNER角色可操作"""
    if current_user.role != UserRole.OWNER:
        raise ForbiddenError("没有权限操作")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("用户", user_id)
    
    user.is_active = True
    await db.commit()
    return {"message": "用户已启用"}

