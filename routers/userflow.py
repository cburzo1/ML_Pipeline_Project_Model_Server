from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError
from models.user_flow import UserFlows
from models.user_flow_update import UserFlowUpdate
from schemas.config_schema import ConfigSchema
from pydantic import BaseModel
from database import SessionLocal
from sqlalchemy.orm import Session

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

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
async def get_flow_by_name(flow_name: str, db: db_dependency, user_id: int = Depends(get_current_user_id)):
    # Query the database for the given flow name
    #flow = db.query(UserFlows).filter(UserFlows.flow_name == flow_name).first()

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

@router.delete("/{flow_name}", status_code=status.HTTP_410_GONE)
async def delete_user_flow_by_name(flow_name: str, db: db_dependency, user_id: int = Depends(get_current_user_id)):

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

def deep_merge(old: dict, new: dict):
    """Recursively merge two dictionaries."""
    for key, value in new.items():
        if isinstance(value, dict) and isinstance(old.get(key), dict):
            deep_merge(old[key], value)
        else:
            old[key] = value
    return old

@router.patch("/{flow_name}", status_code=status.HTTP_200_OK)
async def update_user_flow(flow_name: str, updates: UserFlowUpdate, db: db_dependency, user_id: int = Depends(get_current_user_id)):
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
        current_config = flow.config_json or {}
        flow.config_json = deep_merge(current_config, updates.config_json)

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

@router.post("/train/{flow_name}", status_code=status.HTTP_200_OK)
async def train_model(flow_name: str, db: db_dependency, user_id: int = Depends(get_current_user_id)):
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

    if flow.config_json.get('algorithm') == "lin alg":
        print("linear regression")

        dataset = pd.read_csv("dummy_dataset.csv")
        X = dataset.iloc[:, flow.config_json.get('data_range_X')[0]:flow.config_json.get('data_range_X')[1]].values
        y = dataset.iloc[:, flow.config_json.get('data_range_y')[1]].values

        print(len(X[0]))

        print(X, y)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
        regressor = LinearRegression()
        regressor.fit(X_train, y_train)

        y_pred = regressor.predict(X_test)

        print(y_pred)
        #print(flow.config_json.get('data_range_X')[0])
        #print(flow.config_json.get('data_range_y')[0])


    #print("THIS ::?", flow.user_id, flow.flow_name, type(flow.config_json.get('algorithm')))