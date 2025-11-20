from typing import List, Annotated
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Depends, status
import models
from schemas import ConfigSchema
from pydantic import BaseModel
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

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

@app.post("/user_flows", status_code=status.HTTP_201_CREATED)
async def create_user_flow(user_flow: UserFlowBase, db: db_dependency):
    db_user_flow = models.UserFlows(**user_flow.model_dump())
    db.add(db_user_flow)
    db.commit()
    db.refresh(db_user_flow)  # get auto-generated ID & timestamps

    return {
        "id": db_user_flow.id,
        "user_id": db_user_flow.user_id,
        "flow_name": db_user_flow.flow_name,
        "config_json": db_user_flow.config_json,
        "created_at": db_user_flow.created_at,
        "message": "User flow created successfully"
    }