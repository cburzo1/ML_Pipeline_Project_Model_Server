from fastapi import APIRouter, Depends, status, Header, HTTPException, Body, UploadFile, File
from sqlalchemy.orm import Session

from database import SessionLocal
from typing import Annotated, Union, Dict, List

from services.predict_service import predict_model, predict_model_csv

router = APIRouter(
    prefix="/predict",
    tags=["Predict"]
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

@router.post("/{model_id}", status_code=status.HTTP_200_OK)
async def predict(model_id: str, db: db_dependency, input_data: Union[Dict, List[Dict]] = Body(...), user_id: int = Depends(get_current_user_id)):
    result = predict_model(model_id, input_data, user_id, db)

    return result

@router.post("/{model_id}/csv", status_code=status.HTTP_200_OK)
async def predict_csv(model_id: str, db: db_dependency, file: UploadFile = File(...), user_id: int = Depends(get_current_user_id)):
    result = predict_model_csv(model_id, file, user_id, db)

    return result