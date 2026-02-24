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

@router.get("/{dataset_name}", status_code=status.HTTP_200_OK)
async def get_dataset_by_name(dataset_name: str, db: db_dependency, user_id: int = Depends(get_current_user_id)):
    dataset = (
        db.query(DataSets)
        .filter(
            DataSets.user_id == user_id,
            DataSets.dataset_name == dataset_name
        )
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail=f"the dataset '{dataset_name}' not found"
        )

    return {
        "id": dataset.id,
        "user_id": dataset.user_id,
        "flow_name": dataset.dataset_name,
        "description": dataset.description,
        "row_count": dataset.row_count,
        "created_at": dataset.created_at
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def get_datasets(db: db_dependency, user_id: int = Depends(get_current_user_id)):
    # Query the database for the given flow name
    #flow = db.query(UserFlows).filter(UserFlows.flow_name == flow_name).first()

    datasets = (
        db.query(DataSets)
        .filter(
            DataSets.user_id == user_id
        ).all()
    )

    if not datasets:
        raise HTTPException(
            status_code=404,
            detail=f"user {user_id} has no datasets on record."
        )

    dataset_list = []

    for dataset in datasets:
        dataset_list.append([dataset.dataset_name, dataset.created_at])

    return dataset_list

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_dataset(
    db: db_dependency,
    dataset_name: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id)
):
    if file.filename.lower().endswith(".csv"):
        user_folder = f"bucket/csv/{user_id}"
        os.makedirs(user_folder, exist_ok=True)
        file_loc = f"{user_folder}/{dataset_name}.csv"

        with open(file_loc, "wb") as buffer:
            buffer.write(await file.read())
    else:
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed."
        )

    dataset = pd.read_csv(file_loc)
    row_count = len(dataset)
    schema = {col: str(dtype) for col, dtype in dataset.dtypes.items()}

    new_dataset = DataSets(
        user_id=user_id,
        dataset_name=dataset_name,
        description = description,
        storage_path=file_loc,
        row_count = row_count,
        column_schema = schema
    )

    try:
        db.add(new_dataset)
        db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset '{dataset_name}' already exists for this user."
        )

@router.delete("/{dataset_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset_by_name(dataset_name: str, db: db_dependency, user_id: int = Depends(get_current_user_id)):

    # Query the database for the entry
    dataset = (
        db.query(DataSets)
        .filter(
            DataSets.user_id == user_id,
            DataSets.dataset_name == dataset_name
        )
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail=f"Data set '{dataset_name}' not found for user {user_id}"
        )

    file_loc = dataset.storage_path

    if os.path.exists(file_loc):
        os.remove(file_loc)
        print(f"File '{file_loc}' has been deleted.")

        with os.scandir(f"bucket/csv/{user_id}/") as entries:
            if not any(entries):
                os.rmdir(f"bucket/csv/{user_id}/")
            else:
                print(f"user Folder 'bucket/csv/{user_id}/' does not exist.")
    else:
        print(f"File '{file_loc}' does not exist.")

    db.delete(dataset)
    db.commit()

    return {"detail": "DELETED"}