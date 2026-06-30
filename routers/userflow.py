from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Header
from models.user_flow_update import UserFlowUpdate
from schemas.config_schema import ConfigSchema
from pydantic import BaseModel
from database import SessionLocal
from sqlalchemy.orm import Session
from services.auth_service import get_current_user
from services.userflow_service import get_by_flowname, get_userflows, create_userflow, delete_userflow_by_name, update_userflow

router = APIRouter(
    prefix="/user_flows",
    tags=["User Flows"]
)

class UserFlowBase(BaseModel):
    flow_name: str
    dataset_name: str
    config_json: ConfigSchema

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

@router.get("/{flow_name}", status_code=status.HTTP_200_OK)
async def get_flow_by_name(flow_name: str, db: db_dependency, user_id: str = Depends(get_current_user)):
    result = get_by_flowname(flow_name, db, user_id)

    return result

@router.get("/", status_code=status.HTTP_200_OK)
async def get_user_flows(db: db_dependency, user_id: str = Depends(get_current_user)):

    result = get_userflows(db, user_id, )

    return result

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_flow(user_flow: UserFlowBase, db: db_dependency, user_id: str = Depends(get_current_user)):

    result = create_userflow(user_flow, db, user_id)

    return result

@router.delete("/{flow_name}", status_code=status.HTTP_410_GONE)
async def delete_user_flow_by_name(flow_name: str, db: db_dependency, user_id: str = Depends(get_current_user)):

    result = delete_userflow_by_name(flow_name, db, user_id)

    return result

@router.patch("/{flow_name}", status_code=status.HTTP_200_OK)
async def update_user_flow(flow_name: str, updates: UserFlowUpdate, db: db_dependency, user_id: str = Depends(get_current_user)):
    result = update_userflow(flow_name, updates, db, user_id)

    return result