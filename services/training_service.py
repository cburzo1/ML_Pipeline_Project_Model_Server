import inspect
import os
import uuid
from enum import Enum

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, HTTPException
from pandas.core.dtypes.common import is_bool_dtype, is_numeric_dtype, is_datetime64_any_dtype, is_object_dtype
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.datasets import DataSets
from models.user_flow import UserFlows
from models.trained_models import TrainedModels
from models.training_data import TrainingData
from routers.userflow import db_dependency, get_current_user_id
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

'''class FeatureType(str, Enum):
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TEXT = "text"

def infer_feature_type(col: pd.Series) -> FeatureType:
    dtype = col.dtype

    if is_bool_dtype(dtype):
        return FeatureType.BOOLEAN

    if is_numeric_dtype(dtype):
        return FeatureType.NUMERICAL

    if isinstance(dtype, pd.CategoricalDtype):
        return FeatureType.CATEGORICAL

    if is_datetime64_any_dtype(dtype):
        return FeatureType.DATETIME

    # object fallback (strings, mixed)
    if is_object_dtype(dtype):
        # optional heuristic
        unique_ratio = col.nunique(dropna=True) / max(len(col), 1)
        if unique_ratio < 0.2:
            return FeatureType.CATEGORICAL
        return FeatureType.TEXT

    # Safe default
    return FeatureType.TEXT '''


def train_model(flow_name: str, user_id: int, db: Session):
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

    data_set = db.query(DataSets).filter(
        DataSets.dataset_name == flow.dataset_name
    ).first()

    if not data_set:
        raise HTTPException(
            status_code=404,
            detail=f"Flow '{flow.dataset_name}' for user {user_id} not found."
        )

    if flow.config_json.get('algorithm') == "Linear Regression":
        print("linear regression")
        user_file = f"bucket/{data_set.storage_path}.csv"
        #dataset_name = flow.dataset_name

        dataset = pd.read_csv(user_file)

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
            DTYPE_X = data_set.column_schema.get(column_X) #infer_feature_type(dataset.iloc[rows[0]:rows[1], Col_X])
            y = dataset.iloc[rows[0]:rows[1], Col_y:Col_y + 1].values
            DTYPE_y = data_set.column_schema.get(column_y)#infer_feature_type(dataset.iloc[rows[0]:rows[1], Col_y])

            print("COLS: ", X, y)

            print("COL SCHEMA::",data_set.column_schema.get(column_X))

            if DTYPE_X == "object" or DTYPE_y == "object":
                if DTYPE_X == "object":
                    ct = ColumnTransformer(transformers=[('encoder', OneHotEncoder(), [0])], remainder='passthrough')
                    X = np.array(ct.fit_transform(X).toarray())
                else:
                    ct = ColumnTransformer(transformers=[('encoder', OneHotEncoder(), [0])], remainder='passthrough')
                    y = np.array(ct.fit_transform(y).toarray())
                print(X, "ENCODING APPLIED")

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

            sc = StandardScaler()

            print("TRAINING DATA BEFORE:::", X_train)
            print("TRAINING DATA BEFORE:::", X_test)
            print("__________________________________________________________________")
            print("TRAINING DATA BEFORE:::", y_train)
            print("TRAINING DATA BEFORE:::", y_test)

            X_train = sc.fit_transform(X_train)
            X_test = sc.transform(X_test)
            print("__________________________________________________________________")
            y_train = sc.fit_transform(y_train)
            y_test = sc.transform(y_test)

            print("TRAINING DATA AFTER:::", X_train)
            print("TRAINING DATA AFTER:::", X_test)
            print("---------------------------------------------------------------")
            print("TRAINING DATA AFTER:::", y_train)
            print("TRAINING DATA AFTER:::", y_test)

            regressor = LinearRegression()
            regressor.fit(X_train, y_train)

            model_id = str(uuid.uuid4())

            model_dir = f"bucket/{user_id}/trained_models"
            os.makedirs(model_dir, exist_ok=True)

            model_path = f"{model_dir}/model_{model_id}.pkl"

            y_pred = regressor.predict(X_test)

            print("PREDICTIONS", y_pred)

            mae = mean_absolute_error(y_test, y_pred)
            rmse = mean_squared_error(y_test, y_pred)
            print(rmse)
            r2 = r2_score(y_test, y_pred)

            metrics = {
                "mae": mae,
                "rmse": rmse,
                "r2": r2
            }

            model_bundle = {
                "model": regressor,
                "scaling": sc
            }

            joblib.dump(model_bundle, model_path)

            bundle = joblib.load(model_path)

            print("FROM BUNDLE:: ", bundle.get("model").predict(X_test))

            new_trained_model = TrainedModels(
                id=model_id,
                flow_id=flow.id,
                model_type=flow.config_json.get('algorithm'),
                model_path=model_path,
                metrics_json=metrics
            )

            # try:
            db.add(new_trained_model)
            db.commit()



        else:
            raise HTTPException(
                status_code=400,
                detail="your test_size parameter either does not exist or is invalid"
            )
    else:
        raise HTTPException(
            status_code=404,
            detail="your algorithm does not exist in our collection")

''' except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset '{dataset_name}' already exists for this user."
        )'''
