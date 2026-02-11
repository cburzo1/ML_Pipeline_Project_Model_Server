from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError
from models.datasets import DataSets
from pydantic import BaseModel, ValidationError
from database import SessionLocal
from sqlalchemy.orm import Session
from enum import Enum

router = APIRouter(
    prefix="/datasets",
    tags=["DataSets"]
)

'''class DataSetsBase(BaseModel):
    dataset_name: str
    users_csv_file: bytes'''

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()   # commit here if no exception
    except:
        db.rollback()  # rollback on any exception
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