from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as UploadFileDep, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.quick_save import QuickSave
from app.models.user import User
from app.schemas.quick_save import QuickSaveCreate, QuickSaveResponse, QuickSaveUpdate
from app.services.file_service import upload_to_minio
from app.services.quick_save_service import confirm_save, recognize_content, suggest_projects

router = APIRouter()


@router.post(
    "/text",
    status_code=status.HTTP_201_CREATED,
)
async def create_quick_save_text(
    text: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recognition = await recognize_content("text", text)

    save = QuickSave(
        content_type="text",
        content_text=text,
        recognized_text=recognition.get("recognized_text", ""),
        status="pending",
    )
    db.add(save)
    await db.flush()

    suggestions = await suggest_projects(db, recognition.get("recognized_text", ""))

    return {
        "save": QuickSaveResponse.model_validate(save),
        "suggestions": suggestions,
    }


@router.post(
    "/image",
    status_code=status.HTTP_201_CREATED,
)
async def create_quick_save_image(
    file: UploadFile = UploadFileDep(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()

    storage_key = await upload_to_minio(content, ext="png")

    recognition = await recognize_content("image", content)

    save = QuickSave(
        content_type="image",
        file_key=storage_key,
        recognized_text=recognition.get("recognized_text", ""),
        status="pending",
    )
    db.add(save)
    await db.flush()

    suggestions = await suggest_projects(db, recognition.get("recognized_text", ""))

    return {
        "save": QuickSaveResponse.model_validate(save),
        "suggestions": suggestions,
    }


@router.get("", response_model=list[QuickSaveResponse])
async def list_quick_saves(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(QuickSave)
    if status_filter:
        query = query.where(QuickSave.status == status_filter)

    result = await db.execute(query.order_by(QuickSave.created_at.desc()))
    saves = result.scalars().all()
    return [QuickSaveResponse.model_validate(s) for s in saves]


@router.patch("/{save_id}", response_model=QuickSaveResponse)
async def update_quick_save(
    save_id: int,
    payload: QuickSaveUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QuickSave).where(QuickSave.id == save_id)
    )
    save = result.scalar_one_or_none()
    if save is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="随手存记录不存在")

    if payload.confirmed_project_id is not None:
        save = await confirm_save(db, save_id, payload.confirmed_project_id)

    if payload.status == "deleted":
        save.status = "deleted"

    if payload.recognized_text is not None:
        save.recognized_text = payload.recognized_text

    await db.flush()
    return QuickSaveResponse.model_validate(save)