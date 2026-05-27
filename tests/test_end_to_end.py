import io

API_KEY = {"x-api-key": "KEY123"}


def test_full_user_workflow(client):
    # -------------------------
    # 1. Upload dataset
    # -------------------------
    csv_data = """ID,Feature1,Feature2,Category,Target
1,12.4,5.3,A,24.8
2,15.1,,B,30.2
3,9.8,3.1,C,18.4
4,22.5,11.2,A,40.3
5,17.2,6.4,B, 20.5
"""

    file = io.BytesIO(csv_data.encode())

    # FIX 1: dataset name consistency
    dataset_name = "ok_dataset_5"

    # -------------------------
    # 1. Upload dataset
    # -------------------------
    response = client.post(
        "/datasets/",
        headers=API_KEY,
        data={
            "dataset_name": dataset_name,
            "description": "my first dataset"
        },
        files={"file": ("dummy.csv", file, "text/csv")}
    )

    assert response.status_code == 201

    # -------------------------
    # 2. Create user flow
    # -------------------------
    flow_payload = {
        "flow_name": "flow3",
        "dataset_name": dataset_name,  # FIXED
        "config_json": {
            "algorithm": "Linear Regression",
            "data_range_X": "Feature1",
            "data_range_y": "Target",
            "row_range": [0, 3],
            "test_size": 0.2,
            "missing_data": "mean"
        }
    }

    response = client.post(
        "/user_flows/",
        json=flow_payload,
        headers=API_KEY
    )

    assert response.status_code == 201