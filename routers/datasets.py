import os
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Header, Form, File, UploadFile
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError
from models.datasets import DataSets
from pydantic import BaseModel, ValidationError
from database import SessionLocal
from sqlalchemy.orm import Session
from enum import Enum

import pandas as pd

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

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_dataset(
    db: db_dependency,
    dataset_name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id)
):
    user_folder = f"bucket/csv/{user_id}"
    os.makedirs(user_folder, exist_ok=True)
    file_loc = f"{user_folder}/{dataset_name}.csv"

    with open(file_loc, "wb") as buffer:
        buffer.write(await file.read())

    dataset = pd.read_csv(file_loc)
    row_count = len(dataset)

    new_dataset = DataSets(
        user_id=user_id,
        dataset_name=dataset_name,
        description = description,
        storage_path=file_loc,
        row_count = row_count
    )

    try:
        db.add(new_dataset)
        db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset '{dataset_name}' already exists for this user."
        )

