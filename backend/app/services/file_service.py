import io
import os
import uuid
from datetime import datetime, timedelta

from loguru import logger
from minio import Minio
from minio.error import S3Error
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_minio_client
from app.models.file import File


FILE_TYPE_KEYWORDS = {
    "contract": ["合同", "contract", "moa", "agreement", "协议"],
    "receipt": ["签收", "receipt", "sign", "交付"],
    "wechat_screenshot": ["微信", "wechat", "screenshot", "截图", "聊天"],
    "survey": ["调研", "survey", "背景"],
    "certificate": ["验收", "certificate", "完工", "completed", "确认单"],
    "invoice": ["发票", "invoice", "tax", "账单"],
    "photo": ["照片", "photo", "图片", "picture", "jpg", "png"],
    "other": ["其他", "document", "文档"],
}


def detect_file_type(filename: str) -> str:
    name_lower = filename.lower()
    for file_type, keywords in FILE_TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return file_type
    return "other"


async def upload_to_minio(file_content: bytes, bucket: str = None, ext: str = "") -> str:
    if bucket is None:
        bucket = settings.MINIO_BUCKET

    client = get_minio_client()

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info(f"Created MinIO bucket: {bucket}")

    unique_id = uuid.uuid4().hex[:16]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if ext and not ext.startswith("."):
        ext = f".{ext}"
    storage_key = f"{timestamp}_{unique_id}{ext}"

    client.put_object(
        bucket,
        storage_key,
        io.BytesIO(file_content),
        length=len(file_content),
    )
    logger.info(f"Uploaded file to MinIO: {bucket}/{storage_key}")
    return storage_key


async def get_minio_url(storage_key: str, bucket: str = None, expires: int = 3600) -> str:
    if bucket is None:
        bucket = settings.MINIO_BUCKET

    client = get_minio_client()

    try:
        url = client.presigned_get_object(
            bucket,
            storage_key,
            expires=timedelta(seconds=expires),
        )
        return url
    except S3Error as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise


async def delete_from_minio(storage_key: str, bucket: str = None) -> None:
    if bucket is None:
        bucket = settings.MINIO_BUCKET

    client = get_minio_client()
    try:
        client.remove_object(bucket, storage_key)
        logger.info(f"Deleted file from MinIO: {bucket}/{storage_key}")
    except S3Error as e:
        logger.error(f"Failed to delete MinIO object: {e}")


async def save_file_record(
    db: AsyncSession,
    project_id: int | None,
    file_name: str,
    file_type: str,
    storage_key: str,
    file_size: int,
    mime_type: str,
    uploaded_by: int | None,
) -> File:
    file_record = File(
        project_id=project_id,
        file_name=file_name,
        file_type=file_type,
        storage_key=storage_key,
        file_size=file_size,
        mime_type=mime_type,
        uploaded_by=uploaded_by,
    )
    db.add(file_record)
    await db.flush()
    logger.info(f"Saved file record: id={file_record.id}, name={file_name}")
    return file_record