from datetime import date, datetime

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import TaskDailyUpdate, TaskPhoto, Task


MAX_DAILY_PHOTOS_PER_TASK = 2


async def check_daily_photo_limit(
    db: AsyncSession, task_id: int, target_date: date
) -> int:
    result = await db.execute(
        select(func.count(TaskPhoto.id))
        .join(TaskDailyUpdate, TaskPhoto.update_id == TaskDailyUpdate.id)
        .where(
            TaskDailyUpdate.task_id == task_id,
            func.date(TaskDailyUpdate.update_date) == target_date,
        )
    )
    current_count = result.scalar() or 0
    return current_count


async def upload_photo(
    db: AsyncSession,
    update_id: int,
    file_content: bytes,
    filename: str,
) -> TaskPhoto:
    from app.services.file_service import upload_to_minio

    task_result = await db.execute(
        select(TaskDailyUpdate).where(TaskDailyUpdate.id == update_id)
    )
    update = task_result.scalar_one_or_none()
    if update is None:
        raise ValueError(f"Daily update not found: {update_id}")

    current_count = await check_daily_photo_limit(db, update.task_id, update.update_date)
    if current_count >= MAX_DAILY_PHOTOS_PER_TASK:
        logger.warning(
            f"Photo limit reached for task {update.task_id} on {update.update_date}: "
            f"{current_count}/{MAX_DAILY_PHOTOS_PER_TASK}"
        )
        raise PermissionError(
            f"每日每任务最多上传 {MAX_DAILY_PHOTOS_PER_TASK} 张照片，"
            f"当前已上传 {current_count} 张"
        )

    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    storage_key = await upload_to_minio(file_content, ext=ext)

    photo = TaskPhoto(
        update_id=update_id,
        storage_key=storage_key,
    )
    db.add(photo)
    await db.flush()

    logger.info(
        f"Photo uploaded: task={update.task_id}, update={update_id}, "
        f"date={update.update_date}, key={storage_key}"
    )
    return photo