import io

API_KEY = {"x-api-key": "KEY123"}


def test_prediction_schema_mismatch(client):

    # -------------------------
    # 1. Upload dataset
    # -------------------------
    csv_data = """Feature1,Feature2,Target
1,2,10
2,3,20
3,4,30
4,5,40
5,6,50
"""

    file = io.BytesIO(csv_data.encode())

    dataset_name = "prediction_schema_dataset"

    response = client.post(
        "/datasets/",
        headers=API_KEY,
        data={
            "dataset_name": dataset_name,
            "description": "prediction schema test"
        },
        files={"file": ("dummy.csv", file, "text/csv")}
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code == 201

    # -------------------------
    # 2. Create flow
    # -------------------------
    flow_payload = {
        "flow_name": "prediction_schema_flow",
        "dataset_name": dataset_name,
        "config_json": {
            "algorithm": "Linear Regression",
            "data_range_X": "Feature1",
            "data_range_y": "Target",
            "row_range": [0, 4],
            "test_size": 0.2,
            "missing_data": "mean"
        }
    }

    response = client.post(
        "/user_flows/",
        json=flow_payload,
        headers=API_KEY
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code == 201

    # -------------------------
    # 3. Train model
    # -------------------------
    response = client.post(
        "/train/prediction_schema_flow",
        headers=API_KEY
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code == 200

    model_id = response.json()["model_id"]

    # -------------------------
    # 4. Missing feature
    # -------------------------
    missing_feature_payload = [
        {
            "Feature2": 5.3,
            "Target": 20
        }
    ]

    response = client.post(
        f"/predict/{model_id}",
        json=missing_feature_payload,
        headers=API_KEY
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code in [400, 422, 500]

    # -------------------------
    # 5. Wrong feature name
    # -------------------------
    wrong_feature_payload = [
        {
            "WRONG_FEATURE": 999,
            "Target": 20
        }
    ]

    response = client.post(
        f"/predict/{model_id}",
        json=wrong_feature_payload,
        headers=API_KEY
    )

    print(response.status_code)
    print(response.json())

    assert response.status_code in [400, 422, 500]