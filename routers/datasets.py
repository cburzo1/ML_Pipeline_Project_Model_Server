from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Header, Form, File, UploadFile
from database import SessionLocal
from sqlalchemy.orm import Session
from services.auth_service import get_current_user

from services.datasets_service import get_all_datasets, get_dataset_by_name, create_dataset, delete_dataset

router = APIRouter(
    prefix="/datasets",
    tags=["DataSets"]
)

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

'''@router.get("/{dataset_name}", status_code=status.HTTP_200_OK)
async def get_datasets(dataset_name: str, db: db_dependency, user_id: int = Depends(get_current_user_id)):

    result = get_dataset_by_name(dataset_name, user_id, db)

    return result'''

@router.get("/{dataset_name}", status_code=status.HTTP_200_OK)
async def get_datasets(dataset_name: str, db: db_dependency, user_id: str = Depends(get_current_user)):

    result = get_dataset_by_name(dataset_name, user_id, db)

    return result



@router.get("/", status_code=status.HTTP_200_OK)
async def list_datasets(db: db_dependency, user_id: str = Depends(get_current_user)):

    result = get_all_datasets(user_id, db)

    return result

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_datasets(db: db_dependency, dataset_name: str = Form(...), description: str = Form(None), file: UploadFile = File(...), user_id: str = Depends(get_current_user)):

    print(user_id)

    result = create_dataset(user_id, db, dataset_name, description, file)

    return result


@router.delete("/{dataset_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasets(dataset_name: str, db: db_dependency, user_id: str = Depends(get_current_user)):

    result = delete_dataset(dataset_name, user_id, db)

    return result