from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.security import verify_access_token


def get_minio_client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )


def get_minio_public_client() -> Minio:
    """生成预签名 URL 专用的 MinIO 客户端。

    预签名 URL 的 SigV4 签名会绑定 endpoint 主机名（写入 canonical request 的
    `host`）。浏览器实际访问的是 MINIO_PUBLIC_ENDPOINT（如 localhost:9000），
    因此必须用**公开地址**签名，否则浏览器携带 `Host: localhost:9000` 访问时，
    MinIO 用收到的 Host 重新计算签名，与 URL 中针对 `minio:9000` 计算的签名不一致，
    报 `SignatureDoesNotMatch`。

    该客户端仅用于本地签名（`presigned_get_object` 不发起网络连接），
    故在后端容器内用公开主机名初始化是安全的。
    """
    public_endpoint = getattr(settings, "MINIO_PUBLIC_ENDPOINT", None) or settings.MINIO_ENDPOINT
    return Minio(
        public_endpoint,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise credentials_exception

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise credentials_exception

    token = parts[1]
    try:
        payload = verify_access_token(token)
    except ValueError:
        raise credentials_exception

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role == "disabled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_role(*roles: str) -> Callable:
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: {', '.join(roles)}",
            )
        return current_user

    return role_checker