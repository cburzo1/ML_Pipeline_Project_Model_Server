from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError
from models.user_flow import UserFlows
from models.user_flow_update import UserFlowUpdate
from schemas.config_schema import ConfigSchema
from pydantic import BaseModel, ValidationError
from database import SessionLocal
from sqlalchemy.orm import Session

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.impute import SimpleImputer

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

    '''if updates.config_json:
        current_config = flow.config_json or {}
        flow.config_json = deep_merge(current_config, updates.config_json)'''
    if updates.config_json:
        current_config = flow.config_json or {}
        merged_config = deep_merge(current_config, updates.config_json)

        try:
            # 🔑 THIS is where Literal validation happens
            ConfigSchema.model_validate(merged_config)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=e.errors()
            )

        flow.config_json = merged_config

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

    if flow.config_json.get('algorithm') == "Linear Regression":
        print("linear regression")

        dataset = pd.read_csv("dummy_dataset_missing_data.csv")

        column_X = flow.config_json.get("data_range_X")
        column_y = flow.config_json.get("data_range_y")

        # Too remove. Redundant
        '''if not column_X:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: data_range_X"
            )

        if not column_y:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: data_range_y"
            )'''

        # Existence checks
        missing = []
        if column_X not in dataset.columns:
            missing.append(column_X)

        if column_y not in dataset.columns:
            missing.append(column_y)

        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid column(s): {missing}. Available columns: {list(dataset.columns)}"
            )

        # Safe indexing
        Col_X = dataset.columns.get_loc(column_X)
        Col_y = dataset.columns.get_loc(column_y)

        rows = flow.config_json.get('row_range')

        print(Col_X, Col_y)

        print(rows)

        print(dataset.columns.values, dataset.columns[Col_X])

        X = None
        y = None

        if dataset.columns[Col_X] in dataset.columns.values:
            X = dataset.iloc[rows[0]:rows[1], Col_X:Col_X + 1].values
            y = dataset.iloc[rows[0]:rows[1], Col_y:Col_y + 1].values

            print(X)

            if flow.config_json.get("missing_data"):
                imputer = SimpleImputer(missing_values=np.nan, strategy=flow.config_json.get("missing_data"))

                imputer.fit(X)
                X = imputer.transform(X)
                imputer.fit(y)
                y = imputer.transform(y)
                print("IMPUTED!!::", X, y)

        else:
            raise HTTPException(
                status_code=400,
                detail="Your Feature either doesnt exist in the dataset or you did not specify a feature"
            )

        if flow.config_json.get('test_size') is not None and flow.config_json.get('test_size') > 0 or flow.config_json.get('test_size') <= 1:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=flow.config_json.get('test_size'), random_state=0)
            regressor = LinearRegression()
            regressor.fit(X_train, y_train)

            y_pred = regressor.predict(X_test)

            print(y_pred)
        else:
            raise HTTPException(
                status_code=400,
                detail="your test_size parameter either does not exist or is invalid"
            )
    else:
        raise HTTPException(
            status_code=404,
            detail="your algorithm does not exist in our collection"
        )