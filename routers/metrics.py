from typing import Annotated, List
from fastapi import APIRouter, Depends, status, HTTPException, Header, Query
from pydantic import BaseModel
from services.auth_service import get_current_user
from database import SessionLocal
from sqlalchemy.orm import Session

from services.metrics_service import metrics_with_saved_models

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"]
)

class MetricsCompareRequest(BaseModel):
    model_ida: str
    model_idb: str

def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
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

@router.post("/", status_code=status.HTTP_201_CREATED)
async def compare_metrics_with_saved_models(model_id: MetricsCompareRequest, db: db_dependency, user_id: str = Depends(get_current_user)):

    result = metrics_with_saved_models(user_id, model_id.model_ida, model_id.model_idb, db)

    return result