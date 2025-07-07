from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.ven import VENCreate, VENRead
from app.models.ven import VEN
from app.db.database import database
from sqlalchemy import select

router = APIRouter()

@router.post("/", response_model=VENRead)
async def register_ven(ven: VENCreate):
    query = VEN.__table__.insert().values(**ven.dict())
    await database.execute(query)
    return ven

@router.get("/", response_model=list[VENRead])
async def list_vens():
    query = select(VEN)
    return await database.fetch_all(query)
