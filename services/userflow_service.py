from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from models.datasets import DataSets
from models.user_flow import UserFlows

from schemas.config_schema import ConfigSchema


def get_by_flowname(flow_name: str, db: Session, user_id: str):
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
        "flow_name": flow.flow_name,
        "config_json": flow.config_json,
        "created_at": flow.created_at
    }

def get_userflows(db: Session, user_id: str):
    flows = (
        db.query(UserFlows)
        .filter(
            UserFlows.user_id == user_id
        ).all()
    )

    if not flows:
        return []

    flow_list = []

    for flow in flows:
        flow_list.append({flow.flow_name, flow.created_at})

    return flow_list

def create_userflow(user_flow, db: Session, user_id: str):
    dataset = (
        db.query(DataSets)
        .filter(
            DataSets.user_id == user_id,
            DataSets.dataset_name == user_flow.dataset_name
        )
        .first()
    )

    if not dataset:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{user_flow.dataset_name}' not found"
        )

    flow_data = user_flow.model_dump()
    flow_data.pop("dataset_name", None)

    db_user_flow = UserFlows(
        user_id=user_id,
        dataset_id=dataset.id,
        dataset_name=dataset.dataset_name,
        **flow_data
    )

    db.add(db_user_flow)

    try:
        db.commit()
        db.refresh(db_user_flow)

        return {
            "id": db_user_flow.id,
            "flow_name": db_user_flow.flow_name,
            "dataset_name": dataset.dataset_name,
            "dataset_id": dataset.id,
            "config_json": db_user_flow.config_json,
            "created_at": db_user_flow.created_at,
            "message": "User flow created successfully"
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Flow '{user_flow.flow_name}' already exists"
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

def delete_userflow_by_name(flow_name: str, db: Session, user_id: str):
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
            detail=f"Flow '{flow_name}' not found"
        )

    try:
        db.delete(flow)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete flow"
        )

    return {"detail": "Flow deleted"}

def deep_merge(old: dict, new: dict):
    """Recursively merge two dictionaries."""
    for key, value in new.items():
        if isinstance(value, dict) and isinstance(old.get(key), dict):
            deep_merge(old[key], value)
        else:
            old[key] = value
    return old

def update_userflow(flow_name: str, updates, db: Session, user_id: str):
    flow = db.query(UserFlows).filter(
        UserFlows.user_id == user_id,
        UserFlows.flow_name == flow_name
    ).first()

    if not flow:
        raise HTTPException(
            status_code=404,
            detail=f"Flow '{flow_name}' not found"
        )

    if updates.flow_name is not None:
        flow.flow_name = updates.flow_name

    if updates.config_json:
        current_config = flow.config_json or {}
        merged_config = deep_merge(current_config, updates.config_json)

        try:
            ConfigSchema.model_validate(merged_config)
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=e.errors()
            )

        flow.config_json = merged_config

    try:
        db.commit()
        db.refresh(flow)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update flow"
        )

    return {
        "message": "Flow updated",
        "updated_flow": {
            "id": flow.id,
            "flow_name": flow.flow_name,
            "config_json": flow.config_json,
            "created_at": flow.created_at
        }
    }