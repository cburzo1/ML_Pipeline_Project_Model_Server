import time
from fastapi import HTTPException
import joblib
from sqlalchemy.orm import Session

from models.trained_models import TrainedModels
import pandas as pd

def predict_model(model_id: str, input_data: dict, user_id: int, db: Session):

    trained_model = db.query(TrainedModels).filter(
        TrainedModels.user_id == user_id,
        TrainedModels.id == model_id
    ).first()

    if not trained_model:
        raise HTTPException(
            status_code=404,
            detail=f"model '{model_id}' for user {user_id} not found."
        )

    model_dir = f"bucket/{user_id}/trained_models"
    model_path = f"{model_dir}/model_{model_id}.pkl"

    bundle = joblib.load(model_path)

    feature_order_columns = bundle.get("feature_order")
    model = bundle.get("model")

    if isinstance(input_data, dict):
        input_data = [input_data]

    print(input_data)

    user_input_columns = list(input_data[0].keys())

    if not input_data:
        raise HTTPException(400, "No input data provided")

    print(user_input_columns)

    if set(user_input_columns) != set(feature_order_columns):
        raise HTTPException(
            status_code=400,
            detail="Input features do not match model features."
        )

    X = []

    for row in input_data:
        row_values = []
        for f in feature_order_columns:
            if f not in row:
                raise HTTPException(400, f"Missing feature: {f}")

            row_values.append(float(row[f]))

        X.append(row_values)

    start = time.perf_counter()

    prediction = model.predict(X)

    latency = (time.perf_counter() - start) * 1000

    return {
        "prediction": prediction.tolist(),
        "model_id": model_id,
        "num_predictions": len(prediction),
        "latency_ms": round(latency, 3)
    }

def predict_using_csv(model_id: str, file, user_id: int, db: Session):
    trained_model = db.query(TrainedModels).filter(
        TrainedModels.user_id == user_id,
        TrainedModels.id == model_id
    ).first()

    if not trained_model:
        raise HTTPException(
            status_code=404,
            detail=f"model '{model_id}' for user {user_id} not found."
        )

    model_dir = f"bucket/{user_id}/trained_models"
    model_path = f"{model_dir}/model_{model_id}.pkl"

    bundle = joblib.load(model_path)

    feature_order_columns = bundle.get("feature_order")
    model = bundle.get("model")

    print(file)

    df = pd.read_csv(file.file)

    if df.empty:
        raise HTTPException(400, "CSV file is empty")

    data_dict = df.to_dict(orient='records')

    print(data_dict)

    user_input_columns = list(data_dict[0].keys())

    if set(user_input_columns) != set(feature_order_columns):
        raise HTTPException(
            status_code=400,
            detail="Input features do not match model features."
        )

    X = []

    for i, row in enumerate(data_dict):
        row_values = []

        for f in feature_order_columns:
            if f not in row:
                raise HTTPException(400, f"Row {i}: Missing feature '{f}'")

            if pd.isna(row[f]) or row[f] == "":
                raise HTTPException(400, f"Row {i}: Missing value for '{f}'")

            try:
                value = float(row[f])
            except:
                raise HTTPException(400, f"Row {i}: Invalid type for '{f}'")

            row_values.append(value)

        X.append(row_values)

    start = time.perf_counter()

    prediction = model.predict(X)

    latency = (time.perf_counter() - start) * 1000

    return {
        "prediction": prediction.tolist(),
        "model_id": model_id,
        "num_predictions": len(prediction),
        "latency_ms": round(latency, 3)
    }