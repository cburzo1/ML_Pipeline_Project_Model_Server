import os

import joblib
from sqlalchemy.orm import Session
from models.trained_models import TrainedModels


def metrics_with_saved_models(user_id: int, model_ids, db: Session):
    models = db.query(TrainedModels).filter(
        TrainedModels.user_id == user_id,
        TrainedModels.id.in_(model_ids)
    ).all()

    if not models:
        return []

    metrics_list = []

    model_dir = f"bucket/{user_id}/trained_models"

    for i in range(0, len(models)):
        model_path = f"{model_dir}/model_{models[i].id}.pkl"

        metrics_list.append(joblib.load(model_path).get("metrics"))

    print(metrics_list)

    '''mae = min(metrics_list[0].get('mae'), metrics_list[1].get('mae'))
    rmse = min(metrics_list[0].get('rmse'), metrics_list[1].get('rmse'))
    r2 = max(metrics_list[0].get('r2'), metrics_list[1].get('r2'))'''

    #print(mae, rmse, r2)