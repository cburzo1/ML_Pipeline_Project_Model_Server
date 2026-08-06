import os

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models.datasets import DataSets
from models.user_flow import UserFlows
from services.storage_service import upload_file, delete_file

def get_dataset_by_name(dataset_name: str,user_id: str, db: Session):
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
        "dataset_name": dataset.dataset_name,
        "description": dataset.description,
        "row_count": dataset.row_count,
        "created_at": dataset.created_at
    }

def get_all_datasets(user_id: str, db: Session):
    datasets = (
        db.query(DataSets)
        .filter(
            DataSets.user_id == user_id
        ).all()
    )

    if not datasets:
        return []

    dataset_list = []

    for dataset in datasets:
        dataset_list.append([dataset.dataset_name, dataset.created_at])

    return dataset_list

def create_dataset(user_id: str, db: Session, dataset_name: str, description: str, file):

    # 1. Validate filename
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed."
        )

    # 2. Check if dataset already exists (early reject)
    existing = (
        db.query(DataSets)
        .filter(
            DataSets.user_id == user_id,
            DataSets.dataset_name == dataset_name
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset '{dataset_name}' already exists for this user."
        )

    # 3. Validate CSV BEFORE writing to disk
    try:
        dataset = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV format."
        )

    # 4. Extract metadata
    row_count = len(dataset)
    schema = {col: str(dtype) for col, dtype in dataset.dtypes.items()}

    # 5. Reset file pointer (IMPORTANT)
    file.file.seek(0)

    s3_key = f"{user_id}/csv/{dataset_name}.csv"

    try:
        upload_file(file.file, s3_key)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to upload dataset."
        )

    new_dataset = DataSets(
        user_id=user_id,
        dataset_name=dataset_name,
        description=description,
        storage_path=s3_key,#relative_file_loc
        row_count=row_count,
        column_schema=schema
    )

    try:
        db.add(new_dataset)
        db.commit()

    except IntegrityError:
        db.rollback()

        try:
            delete_file(s3_key)
        except Exception:
            pass

        raise HTTPException(
            status_code=400,
            detail=f"Dataset '{dataset_name}' already exists for this user."
        )

    except Exception:
        db.rollback()

        try:
            delete_file(s3_key)
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail="Failed to create dataset."
        )

    return {
        "dataset_name": dataset_name,
        "row_count": row_count
    }

def delete_dataset(dataset_name: str, user_id: str, db: Session):
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

    flow = (
        db.query(UserFlows)
        .filter(
            UserFlows.user_id == user_id,
            UserFlows.dataset_name == dataset_name
        )
        .first()
    )

    if not flow:
        raise HTTPException(
            status_code=404,
            detail=f"User flow with dataset '{dataset_name}' was not found"
        )

    if flow.dataset_name == dataset_name:
        raise HTTPException(
            status_code=404,
            detail=f"{dataset_name} ' is bound to user_flow configuration {flow.flow_name}"
        )

    s3_key = f"{user_id}/csv/{dataset_name}.csv"

    # Delete the file from S3
    try:
        delete_file(s3_key)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete dataset file from storage."
        )

    # Delete the database record
    try:
        db.delete(dataset)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete dataset from database."
        )

    return {"detail": "DELETED"}