from fastapi import APIRouter, Depends, status, Header, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from typing import Annotated

from services.training_service import train_model
from routers.datasets import get_current_user_id

router = APIRouter(
    prefix="/train",
    tags=["Training"]
)

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

USER_KEYS = {
    "KEY123": 1,
    "KEY456": 2,
    "KEY789": 3
}

def get_current_user_id(x_api_key: str = Header(None)):
    if x_api_key not in USER_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return USER_KEYS[x_api_key]

@router.post("/{flow_name}", status_code=status.HTTP_200_OK)
async def train(flow_name: str, db: db_dependency, user_id: int = Depends(get_current_user_id)):

    result = train_model(flow_name, user_id, db)

    return result