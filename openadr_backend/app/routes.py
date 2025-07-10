from fastapi import APIRouter, Depends
from .models import VEN
from .crud import create_ven
from .db.database import get_session

router = APIRouter()

@router.post("/vens/")
async def register_ven(ven: VEN, session=Depends(get_session)):
    return await create_ven(session, ven)
