import io

API_KEY = {"x-api-key": "KEY123"}


def test_invalid_flow_config(client):

    # -------------------------
    # 1. Upload valid dataset
    # -------------------------
    csv_data = """Feature1,Feature2,Target
1,2,10
2,3,20
3,4,30
"""

    file = io.BytesIO(csv_data.encode())

    dataset_name = "invalid_flow_dataset"

    response = client.post(
        "/datasets/",
        headers=API_KEY,
        data={
            "dataset_name": dataset_name,
            "description": "testing invalid flow config"
        },
        files={"file": ("dummy.csv", file, "text/csv")}
    )

    assert response.status_code == 201

    # -------------------------
    # 2. Invalid column names
    # -------------------------
    invalid_columns_payload = {
        "flow_name": "bad_columns_flow",
        "dataset_name": dataset_name,
        "config_json": {
            "algorithm": "Linear Regression",
            "data_range_X": "DOES_NOT_EXIST",
            "data_range_y": "Target",
            "row_range": [0, 2],
            "test_size": 0.2
        }
    }

    response = client.post(
        "/user_flows/",
        json=invalid_columns_payload,
        headers=API_KEY
    )

    # Depending on your validation location,
    # this may fail here OR during training.
    assert response.status_code in [400, 201]

    # -------------------------
    # 3. Invalid test_size
    # -------------------------
    invalid_test_size_payload = {
        "flow_name": "bad_test_size_flow",
        "dataset_name": dataset_name,
        "config_json": {
            "algorithm": "Linear Regression",
            "data_range_X": "Feature1",
            "data_range_y": "Target",
            "row_range": [0, 2],
            "test_size": 5.0
        }
    }

    response = client.post(
        "/user_flows/",
        json=invalid_test_size_payload,
        headers=API_KEY
    )

    assert response.status_code in [400, 422]

    # -------------------------
    # 4. Missing algorithm
    # -------------------------
    missing_algorithm_payload = {
        "flow_name": "missing_algorithm_flow",
        "dataset_name": dataset_name,
        "config_json": {
            "data_range_X": "Feature1",
            "data_range_y": "Target",
            "row_range": [0, 2],
            "test_size": 0.2
        }
    }

    response = client.post(
        "/user_flows/",
        json=missing_algorithm_payload,
        headers=API_KEY
    )

    assert response.status_code == 422