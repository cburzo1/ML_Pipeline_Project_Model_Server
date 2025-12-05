from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError

from models.user_flow import UserFlows
from models.user_flow_update import UserFlowUpdate
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

@router.get("/{flow_name}", status_code=status.HTTP_200_OK)
async def get_user_flow_by_name(flow_name: str, db: db_dependency):
    # Query the database for the given flow name
    flow = db.query(UserFlows).filter(UserFlows.flow_name == flow_name).first()

    if not flow:
        raise HTTPException(
            status_code=404,
            detail=f"User flow '{flow_name}' not found"
        )

    return {
        "id": flow.id,
        "user_id": flow.user_id,
        "flow_name": flow.flow_name,
        "config_json": flow.config_json,
        "created_at": flow.created_at
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_flow(user_flow: UserFlowBase, db: db_dependency):
    db_user_flow = UserFlows(**user_flow.model_dump())
    db.add(db_user_flow)

    try:
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

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="A flow with this name already exists!"
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

@router.delete("/{user_id}/{flow_name}", status_code=status.HTTP_410_GONE)
async def delete_user_flow_by_name(flow_name: str, user_id: int, db: db_dependency):

    # Query the database for the entry
    flow = (
        db.query(UserFlows)
        .filter(
            UserFlows.user_id == user_id,
            UserFlows.flow_name == flow_name
        )
        .first()
    )

    if not flow:
        raise HTTPException(
            status_code=404,
            detail=f"User flow '{flow_name}' not found for user {user_id}"
        )

    db.delete(flow)
    db.commit()

    return {"detail": "DELETED"}

def shallow_merge(old: dict, new: dict):
    for key, value in new.items():
        # If both sides are dicts → merge one nested level
        if isinstance(value, dict) and isinstance(old.get(key), dict):
            for nested_key, nested_value in value.items():
                old[key][nested_key] = nested_value

        # Otherwise overwrite the value
        else:
            old[key] = value

    return old

@router.patch("/{user_id}/{flow_name}", status_code=status.HTTP_200_OK)
async def update_user_flow(
    user_id: int,
    flow_name: str,
    updates: UserFlowUpdate,
    db: db_dependency
):
    # Locate the correct flow
    flow = db.query(UserFlows).filter(
        UserFlows.user_id == user_id,
        UserFlows.flow_name == flow_name
    ).first()

    if not flow:
        raise HTTPException(
            status_code=404,
            detail=f"Flow '{flow_name}' for user {user_id} not found."
        )

    # Apply updates
    if updates.flow_name is not None:
        flow.flow_name = updates.flow_name

    if updates.config_json:
        current = dict(flow.config_json or {}) 
        flow.config_json = shallow_merge(current, updates.config_json)

    db.commit()
    db.refresh(flow)

    return {
        "message": "Flow updated",
        "updated_flow": {
            "id": flow.id,
            "user_id": flow.user_id,
            "flow_name": flow.flow_name,
            "config_json": flow.config_json,
            "created_at": flow.created_at
        }
    }