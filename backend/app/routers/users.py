from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_users():
    return {"items": [], "total": 0}


@router.post("")
async def create_user():
    return {"message": "Create user endpoint"}