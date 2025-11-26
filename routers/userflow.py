from typing import Annotated
from fastapi import APIRouter, Depends, status
from models.user_flow import UserFlows
from schemas.config_schema import ConfigSchema
from pydantic import BaseModel
from database import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/user_flows",
    tags=["User Flows"]
)

class UserFlowBase(BaseModel):
    user_id: int
    flow_name: str
    config_json: ConfigSchema

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_flow(user_flow: UserFlowBase, db: db_dependency):
    db_user_flow = UserFlows(**user_flow.model_dump())
    db.add(db_user_flow)
    db.commit()
    db.refresh(db_user_flow)

    return {
        "id": db_user_flow.id,
        "user_id": db_user_flow.user_id,
        "flow_name": db_user_flow.flow_name,
        "config_json": db_user_flow.config_json,
        "created_at": db_user_flow.created_at,
        "message": "User flow created successfully"
    }