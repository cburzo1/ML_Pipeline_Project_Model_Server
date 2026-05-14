import os
import uuid

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.orm import Session

from models.datasets import DataSets
from models.user_flow import UserFlows
from models.trained_models import TrainedModels
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def delete_model(model_id: str, user_id: int, db: Session):
    trained_model = db.query(TrainedModels).filter(
        TrainedModels.user_id == user_id,
        TrainedModels.id == model_id
    ).first()

    if not trained_model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found."
        )

    file_loc = f"bucket/{trained_model.model_path}"

    if os.path.exists(file_loc):
        os.remove(file_loc)
        print(f"File '{file_loc}' has been deleted.")

    else:
        print(f"File '{file_loc}' does not exist.")

    trained_model_dir = f"bucket/{user_id}/trained_models"

    if os.path.exists(trained_model_dir):
        with os.scandir(trained_model_dir) as entries:
            if not any(entries):
                os.rmdir(trained_model_dir)
            else:
                print(f"Folder '{trained_model_dir}' is not empty.")

    user_dir = f"bucket/{user_id}"

    if os.path.exists(user_dir):
        with os.scandir(user_dir) as entries:
            if not any(entries):
                os.rmdir(user_dir)
            else:
                print(f"Folder '{user_dir}' is not empty.")

    try:
        db.delete(trained_model)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete model"
        )

    return {"detail": "Model deleted"}

def get_all_models(user_id: int, db: Session):
    trained_models = db.query(TrainedModels).filter(
        TrainedModels.user_id == user_id
    ).all()

    if not trained_models:
        return []

    trained_models_list = []

    for model in trained_models:
        trained_models_list.append({
            "model_id": model.id
        })

    return trained_models_list

def prepare_data(flow, data_set_meta):
    user_file = f"bucket/{data_set_meta.storage_path}.csv"
    df = pd.read_csv(user_file)

    column_X = flow.config_json.get("data_range_X")
    column_y = flow.config_json.get("data_range_y")

    # Validate columns
    missing = []
    if column_X not in df.columns:
        missing.append(column_X)
    if column_y not in df.columns:
        missing.append(column_y)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid column(s): {missing}. Available columns: {list(df.columns)}"
        )

    rows = flow.config_json.get('row_range')

    X = df.iloc[rows[0]:rows[1]][[column_X]].values
    y = df.iloc[rows[0]:rows[1]][[column_y]].values

    # Encoding (basic)
    DTYPE_X = data_set_meta.column_schema.get(column_X)
    DTYPE_y = data_set_meta.column_schema.get(column_y)

    if DTYPE_X == "object":
        ct = ColumnTransformer(
            transformers=[('encoder', OneHotEncoder(), [0])],
            remainder='passthrough'
        )
        X = np.array(ct.fit_transform(X).toarray())

    if DTYPE_y == "object":
        ct = ColumnTransformer(
            transformers=[('encoder', OneHotEncoder(), [0])],
            remainder='passthrough'
        )
        y = np.array(ct.fit_transform(y).toarray())

    # Missing data
    if flow.config_json.get("missing_data"):
        imputer = SimpleImputer(
            missing_values=np.nan,
            strategy=flow.config_json.get("missing_data")
        )
        X = imputer.fit_transform(X)
        y = imputer.fit_transform(y)

    return X, y, [column_X]

def train_linear_regression(X, y, flow):
    test_size = flow.config_json.get("test_size")

    if test_size is None or not (0 < test_size <= 1):
        raise HTTPException(
            status_code=400,
            detail="Invalid test_size"
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=0
    )

    sc = StandardScaler()

    X_train = sc.fit_transform(X_train)
    X_test = sc.transform(X_test)
    y_train = sc.fit_transform(y_train)
    y_test = sc.transform(y_test)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    metrics = {
        "mae": mean_absolute_error(y_test, y_pred),
        "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
        "r2": r2_score(y_test, y_pred)
    }

    return model, sc, metrics

def train_model(flow_name: str, user_id: int, db: Session):
    flow = db.query(UserFlows).filter(
        UserFlows.user_id == user_id,
        UserFlows.flow_name == flow_name
    ).first()

    if not flow:
        raise HTTPException(404, f"Flow '{flow_name}' not found")

    data_set = db.query(DataSets).filter(
        DataSets.dataset_name == flow.dataset_name
    ).first()

    if not data_set:
        raise HTTPException(404, f"Dataset '{flow.dataset_name}' not found")

    # Step 1: preprocess
    X, y, feature_order = prepare_data(flow, data_set)

    # Step 2: train model
    if flow.config_json.get('algorithm') == "Linear Regression":
        model, sc, metrics = train_linear_regression(X, y, flow)
    else:
        raise HTTPException(400, "Unsupported algorithm")

    # Step 3: persist
    model_id = str(uuid.uuid4())

    model_dir = f"bucket/{user_id}/trained_models"
    os.makedirs(model_dir, exist_ok=True)

    model_path = f"{model_dir}/model_{model_id}.pkl"
    relative_file_loc = f"/{user_id}/trained_models/model_{model_id}.pkl"

    bundle = {
        "model": model,
        "scaling": sc,
        "feature_order": feature_order,
        "metrics": metrics
    }

    joblib.dump(bundle, model_path)

    new_model = TrainedModels(
        id=model_id,
        flow_id=flow.id,
        user_id=user_id,
        model_type=flow.config_json.get('algorithm'),
        model_path=relative_file_loc,
        metrics_json=metrics
    )

    try:
        db.add(new_model)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, "Failed to save model")

    return {
        "model_id": model_id,
        "metrics": metrics
    }
