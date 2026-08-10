from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as UploadFileDep, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.brokerage import (
    BrokerageCommercial,
    BrokerageContract,
    BrokerageSurvey,
    RepairBrokerage,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.brokerage import (
    BrokerageCommercialCreate,
    BrokerageCommercialResponse,
    BrokerageContractCreate,
    BrokerageContractResponse,
    BrokerageSurveyCreate,
    BrokerageSurveyResponse,
    RepairBrokerageCreate,
    RepairBrokerageResponse,
)
from app.services.file_service import upload_to_minio

router = APIRouter()


@router.get(
    "/projects/{project_id}/surveys",
    response_model=BrokerageSurveyResponse,
)
async def get_survey(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerageSurvey).where(BrokerageSurvey.project_id == project_id)
    )
    survey = result.scalar_one_or_none()
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="调研信息不存在")
    return BrokerageSurveyResponse.model_validate(survey)


@router.post(
    "/projects/{project_id}/surveys",
    response_model=BrokerageSurveyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_survey(
    project_id: int,
    payload: BrokerageSurveyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    survey = BrokerageSurvey(
        project_id=project_id,
        conclusion=payload.conclusion,
        survey_detail=payload.survey_detail,
    )
    db.add(survey)
    await db.flush()
    return BrokerageSurveyResponse.model_validate(survey)


@router.patch(
    "/projects/{project_id}/surveys",
    response_model=BrokerageSurveyResponse,
)
async def update_survey(
    project_id: int,
    payload: BrokerageSurveyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerageSurvey).where(BrokerageSurvey.project_id == project_id)
    )
    survey = result.scalar_one_or_none()
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="调研信息不存在")

    if payload.conclusion is not None:
        survey.conclusion = payload.conclusion
    if payload.survey_detail is not None:
        survey.survey_detail = payload.survey_detail
    await db.flush()
    return BrokerageSurveyResponse.model_validate(survey)


@router.delete(
    "/projects/{project_id}/surveys",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_survey(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerageSurvey).where(BrokerageSurvey.project_id == project_id)
    )
    survey = result.scalar_one_or_none()
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="调研信息不存在")
    await db.delete(survey)


@router.get(
    "/projects/{project_id}/commercials",
    response_model=BrokerageCommercialResponse,
)
async def get_commercial(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerageCommercial).where(BrokerageCommercial.project_id == project_id)
    )
    commercial = result.scalar_one_or_none()
    if commercial is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商务信息不存在")
    return BrokerageCommercialResponse.model_validate(commercial)


@router.post(
    "/projects/{project_id}/commercials",
    response_model=BrokerageCommercialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_commercial(
    project_id: int,
    payload: BrokerageCommercialCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    commercial = BrokerageCommercial(
        project_id=project_id,
        quote_amount=payload.quote_amount,
        commission_amount=payload.commission_amount,
        payment_status=payload.payment_status,
    )
    db.add(commercial)
    await db.flush()
    return BrokerageCommercialResponse.model_validate(commercial)


@router.patch(
    "/projects/{project_id}/commercials",
    response_model=BrokerageCommercialResponse,
)
async def update_commercial(
    project_id: int,
    payload: BrokerageCommercialCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerageCommercial).where(BrokerageCommercial.project_id == project_id)
    )
    commercial = result.scalar_one_or_none()
    if commercial is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商务信息不存在")

    commercial.quote_amount = payload.quote_amount
    commercial.commission_amount = payload.commission_amount
    commercial.payment_status = payload.payment_status
    await db.flush()
    return BrokerageCommercialResponse.model_validate(commercial)


@router.get(
    "/projects/{project_id}/contracts",
    response_model=BrokerageContractResponse,
)
async def get_contract(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(BrokerageContract).where(BrokerageContract.project_id == project_id)
    )
    contract = result.scalar_one_or_none()
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同信息不存在")
    return BrokerageContractResponse.model_validate(contract)


@router.post(
    "/projects/{project_id}/contracts",
    response_model=BrokerageContractResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_contract(
    project_id: int,
    file: UploadFile = UploadFileDep(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    content = await file.read()
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "pdf"
    storage_key = await upload_to_minio(content, ext=ext)

    contract = BrokerageContract(
        project_id=project_id,
        moa_file_key=storage_key,
    )
    db.add(contract)
    await db.flush()
    return BrokerageContractResponse.model_validate(contract)


@router.get(
    "/projects/{project_id}/repair-brokerage",
    response_model=RepairBrokerageResponse,
)
async def get_repair_brokerage(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RepairBrokerage).where(RepairBrokerage.project_id == project_id)
    )
    repair = result.scalar_one_or_none()
    if repair is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="修船经纪信息不存在")
    return RepairBrokerageResponse.model_validate(repair)


@router.post(
    "/projects/{project_id}/repair-brokerage",
    response_model=RepairBrokerageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_repair_brokerage(
    project_id: int,
    payload: RepairBrokerageCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    repair = RepairBrokerage(
        project_id=project_id,
        shipyard_quote=payload.shipyard_quote,
        contract_file_key=payload.contract_file_key,
        handed_over=False,
    )
    db.add(repair)
    await db.flush()
    return RepairBrokerageResponse.model_validate(repair)


@router.patch(
    "/projects/{project_id}/repair-brokerage",
    response_model=RepairBrokerageResponse,
)
async def update_repair_brokerage(
    project_id: int,
    payload: RepairBrokerageCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RepairBrokerage).where(RepairBrokerage.project_id == project_id)
    )
    repair = result.scalar_one_or_none()
    if repair is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="修船经纪信息不存在")

    repair.shipyard_quote = payload.shipyard_quote
    if payload.contract_file_key is not None:
        repair.contract_file_key = payload.contract_file_key
    await db.flush()
    return RepairBrokerageResponse.model_validate(repair)


@router.post(
    "/projects/{project_id}/repair-brokerage/{repair_id}/handover",
    response_model=RepairBrokerageResponse,
)
async def handover_repair_to_supervision(
    project_id: int,
    repair_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RepairBrokerage).where(
            RepairBrokerage.project_id == project_id,
            RepairBrokerage.id == repair_id,
        )
    )
    repair = result.scalar_one_or_none()
    if repair is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="修船经纪信息不存在")

    if repair.handed_over:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该项目已移交监修",
        )

    repair.handed_over = True
    repair.handed_over_at = datetime.utcnow()
    await db.flush()
    return RepairBrokerageResponse.model_validate(repair)