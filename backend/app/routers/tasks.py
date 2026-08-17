from datetime import date, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.dependencies import get_current_user, get_db
from app.models.project import Project
from app.models.task import Task, TaskDailyUpdate, TaskPhoto, TaskStatus
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskDailyUpdateCreate,
    TaskDailyUpdateResponse,
    TaskPhotoUploadResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.photo_service import check_daily_photo_limit, upload_photo as svc_upload_photo
from app.services.file_service import get_minio_url

router = APIRouter()


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
async def list_project_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.sort_order, Task.id)
    )
    tasks = result.scalars().all()
    return [TaskResponse.model_validate(t) for t in tasks]


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: int,
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    max_order_result = await db.execute(
        select(func.max(Task.sort_order)).where(Task.project_id == project_id)
    )
    max_order = max_order_result.scalar() or 0

    task = Task(
        project_id=project_id,
        name=payload.name,
        planned_end_date=payload.planned_end_date,
        status=payload.status.value if isinstance(payload.status, TaskStatus) else payload.status,
        sort_order=max_order + 1,
    )
    db.add(task)
    await db.flush()

    return TaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and isinstance(value, TaskStatus):
            setattr(task, field, value.value)
        else:
            setattr(task, field, value)

    task.updated_at = datetime.utcnow()
    await db.flush()

    return TaskResponse.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    await db.delete(task)


@router.get(
    "/{task_id}/daily-updates",
    response_model=list[TaskDailyUpdateResponse],
)
async def list_daily_updates(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TaskDailyUpdate)
        .options(joinedload(TaskDailyUpdate.photos))
        .where(TaskDailyUpdate.task_id == task_id)
        .order_by(TaskDailyUpdate.update_date.desc())
    )
    updates = result.unique().scalars().all()
    return [TaskDailyUpdateResponse.model_validate(u) for u in updates]


@router.post(
    "/{task_id}/daily-updates",
    response_model=TaskDailyUpdateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_daily_update(
    task_id: int,
    payload: TaskDailyUpdateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    task_result = await db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    update = TaskDailyUpdate(
        task_id=task_id,
        update_date=payload.update_date,
        status=payload.status,
        remark=payload.remark,
        audio_duration=payload.audio_duration,
    )
    db.add(update)
    await db.flush()
    await db.refresh(update, ["photos"])

    # 实时推送：通知该项目在线用户「现场更新已提交」
    try:
        from app.ws import manager

        pid_result = await db.execute(select(Task.project_id).where(Task.id == task_id))
        project_id = pid_result.scalar_one_or_none()
        if project_id is not None:
            await manager.broadcast(
                project_id,
                {
                    "type": "daily_update_created",
                    "task_id": task_id,
                    "update_id": update.id,
                    "update_date": str(update.update_date),
                },
            )
    except Exception:
        # 推送失败不影响主流程
        pass

    return TaskDailyUpdateResponse.model_validate(update)


@router.post(
    "/daily-updates/{update_id}/photos",
    response_model=TaskPhotoUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_daily_update_photo(
    update_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    content = await file.read()
    try:
        photo = await svc_upload_photo(db, update_id, content, file.filename or "photo.jpg")
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return TaskPhotoUploadResponse(
        id=photo.id,
        update_id=photo.update_id,
        storage_key=photo.storage_key,
        created_at=photo.created_at,
    )


@router.delete("/task-photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(TaskPhoto).where(TaskPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="照片不存在")

    await db.delete(photo)


@router.get("/task-photos/{photo_id}/url")
async def get_task_photo_url(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(TaskPhoto).where(TaskPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="照片不存在"
        )
    url = await get_minio_url(photo.storage_key)
    return {"url": url}