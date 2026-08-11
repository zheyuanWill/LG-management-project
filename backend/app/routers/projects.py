from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import generate_project_number, get_project_stats

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    ship_name: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = select(Project)

    if type:
        query = query.where(Project.type == type)
    if status:
        query = query.where(Project.status == status)
    if ship_name:
        query = query.where(Project.ship_name.contains(ship_name))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.execute(count_query)
    total = total.scalar() or 0

    query = query.order_by(Project.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in items],
        total=total,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project_no = await generate_project_number(db, payload.type.value)

    project = Project(
        project_no=project_no,
        type=payload.type.value,
        status="active",
        ship_name=payload.ship_name,
        imo=payload.imo,
        owner_id=payload.owner_id,
        planned_completion_date=payload.planned_completion_date,
        remarks=payload.remarks,
    )
    db.add(project)
    await db.flush()

    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    response = ProjectResponse.model_validate(project)
    return response


@router.get("/{project_id}/stats")
async def get_project_detail(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    base = ProjectResponse.model_validate(project)
    stats = await get_project_stats(db, project_id)
    return {
        **base.model_dump(),
        "stats": stats,
    }


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.utcnow()
    await db.flush()

    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", response_model=ProjectResponse)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    project.status = ProjectStatus.CANCELLED.value
    project.updated_at = datetime.utcnow()
    await db.flush()

    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/handover-to-supervision", response_model=ProjectResponse)
async def handover_to_supervision(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    if project.type != ProjectType.BROKERAGE_REPAIR.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有修船经纪项目可以移交监修",
        )

    project.type = ProjectType.SUPERVISION.value
    project.status = ProjectStatus.ACTIVE.value
    project.updated_at = datetime.utcnow()

    from app.models.task import Task

    default_tasks = [
        Task(
            project_id=project.id,
            name="进厂检验",
            status="not_started",
            sort_order=1,
        ),
        Task(
            project_id=project.id,
            name="船级社检查",
            status="not_started",
            sort_order=2,
        ),
        Task(
            project_id=project.id,
            name="设备维修",
            status="not_started",
            sort_order=3,
        ),
        Task(
            project_id=project.id,
            name="试航验收",
            status="not_started",
            sort_order=4,
        ),
        Task(
            project_id=project.id,
            name="出厂交付",
            status="not_started",
            sort_order=5,
        ),
    ]
    db.add_all(default_tasks)
    await db.flush()

    return ProjectResponse.model_validate(project)