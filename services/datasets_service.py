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
    if file.filename.lower().endswith(".csv"):
        user_folder = f"bucket/{user_id}/csv"
        os.makedirs(user_folder, exist_ok=True)
        file_loc = f"{user_folder}/{dataset_name}.csv"

        with open(file_loc, "wb") as buffer:
            buffer.write(file.file.read())
    else:
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are allowed."
        )

    dataset = pd.read_csv(file_loc)
    row_count = len(dataset)
    schema = {col: str(dtype) for col, dtype in dataset.dtypes.items()}
    relative_file_loc = f"{user_id}/csv/{dataset_name}"

    new_dataset = DataSets(
        user_id=user_id,
        dataset_name=dataset_name,
        description = description,
        storage_path=relative_file_loc,
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

    return {
        "dataset_name": dataset_name,
        "row_count": row_count
    }

def delete_dataset(dataset_name: str,user_id: int, db: Session):
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

    if os.path.exists(file_loc):
        os.remove(file_loc)
        print(f"File '{file_loc}' has been deleted.")

        with os.scandir(f"bucket/{user_id}/csv") as entries:
            if not any(entries):
                os.rmdir(f"bucket/{user_id}/csv")
            else:
                print(f"user Folder 'bucket/{user_id}/csv' does not exist.")
    else:
        print(f"File '{file_loc}' does not exist.")

    db.delete(dataset)
    db.commit()

    return {"detail": "DELETED"}