import os

import joblib
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.trained_models import TrainedModels

def metrics_with_saved_models(user_id: int, model_id_a, model_id_b, db: Session):
    model_a = db.query(TrainedModels).filter(
        TrainedModels.user_id == user_id,
        TrainedModels.id == model_id_a
    ).first()

    if not model_a:
        raise HTTPException(
            status_code=404,
            detail=f"model '{model_id_a}' not found."
        )

    model_b = db.query(TrainedModels).filter(
        TrainedModels.user_id == user_id,
        TrainedModels.id == model_id_b
    ).first()

    if not model_b:
        raise HTTPException(
            status_code=404,
            detail=f"model '{model_id_b}' not found."
        )

    model_dir = f"bucket/{user_id}/trained_models"

    model_a_path = f"{model_dir}/model_{model_a.id}.pkl"
    metrics_model_a = joblib.load(model_a_path).get("metrics")

    model_b_path = f"{model_dir}/model_{model_b.id}.pkl"
    metrics_model_b = joblib.load(model_b_path).get("metrics")

    if not metrics_model_a or not metrics_model_b:
        raise HTTPException(
            status_code=500,
            detail="Model metrics missing from bundle"
        )

    decider = {
        "model_a": 0,
        "model_b": 0
    }

    metric_winners = {}

    # MAE (lower is better)
    if metrics_model_a.get('mae') < metrics_model_b.get('mae'):
        decider["model_a"] += 1
        metric_winners["mae"] = model_a.id
    else:
        decider["model_b"] += 1
        metric_winners["mae"] = model_b.id

    # RMSE (lower is better)
    if metrics_model_a.get('rmse') < metrics_model_b.get('rmse'):
        decider["model_a"] += 1
        metric_winners["rmse"] = model_a.id
    else:
        decider["model_b"] += 1
        metric_winners["rmse"] = model_b.id

    # R2 (higher is better)
    if metrics_model_a.get('r2') > metrics_model_b.get('r2'):
        decider["model_a"] += 1
        metric_winners["r2"] = model_a.id
    else:
        decider["model_b"] += 1
        metric_winners["r2"] = model_b.id

    better_model = None

    if decider["model_a"] > decider["model_b"]:
        better_model = model_a.id

    elif decider["model_b"] > decider["model_a"]:
        better_model = model_b.id

    return {
        "model_a": {
            "model_id": model_a.id,
            "metrics": metrics_model_a
        },

        "model_b": {
            "model_id": model_b.id,
            "metrics": metrics_model_b
        },

        "metric_winners": metric_winners,

        "score": {
            model_a.id: decider["model_a"],
            model_b.id: decider["model_b"]
        },

        "better_model": better_model
    }