import os

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from models.datasets import DataSets


def get_dataset_by_name(dataset_name: str,user_id: int, db: Session):
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

def get_all_datasets(user_id: int, db: Session):
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

def create_dataset(user_id: int, db: Session, dataset_name: str, description: str, file):

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

    # 6. Write file to disk
    user_folder = f"bucket/{user_id}/csv"
    os.makedirs(user_folder, exist_ok=True)
    file_loc = f"{user_folder}/{dataset_name}.csv"

    with open(file_loc, "wb") as buffer:
        buffer.write(file.file.read())

    # 7. Store relative path (clean format)
    relative_file_loc = f"{user_id}/csv/{dataset_name}"

    new_dataset = DataSets(
        user_id=user_id,
        dataset_name=dataset_name,
        description=description,
        storage_path=relative_file_loc,
        row_count=row_count,
        column_schema=schema
    )

    # 8. DB insert (with safety net)
    try:
        db.add(new_dataset)
        db.commit()
    except IntegrityError:
        db.rollback()

        # Optional: cleanup (should rarely happen now, but safe)
        if os.path.exists(file_loc):
            os.remove(file_loc)

        raise HTTPException(
            status_code=400,
            detail=f"Dataset '{dataset_name}' already exists for this user."
        )

    return {
        "dataset_name": dataset_name,
        "row_count": row_count
    }

def delete_dataset(dataset_name: str, user_id: int, db: Session):
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

    file_loc = f"bucket/{dataset.storage_path}.csv"

    # 1. Delete from DB FIRST
    try:
        db.delete(dataset)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete dataset from database."
        )

    # 2. Then delete file (best effort)
    if os.path.exists(file_loc):
        os.remove(file_loc)
        print(f"File '{file_loc}' has been deleted.")

        user_folder = f"bucket/{user_id}/csv"

        if os.path.exists(user_folder):
            with os.scandir(user_folder) as entries:
                if not any(entries):
                    os.rmdir(user_folder)
                else:
                    print(f"Folder '{user_folder}' is not empty.")
    else:
        print(f"File '{file_loc}' does not exist.")

    return {"detail": "DELETED"}