import io

API_KEY = {"x-api-key": "KEY123"}


def test_reject_non_csv_upload(client):

    fake_txt = io.BytesIO(b"This is not a csv file")

    response = client.post(
        "/datasets/",
        headers=API_KEY,
        data={
            "dataset_name": "bad_file_dataset",
            "description": "invalid file type"
        },
        files={
            "file": ("bad.txt", fake_txt, "text/plain")
        }
    )

    assert response.status_code == 400


def test_reject_malformed_csv(client):

    malformed_csv = """ID,Feature1,Target
1,12.4
2,15.1,30.2,EXTRA_COLUMN
3
"""

    file = io.BytesIO(malformed_csv.encode())

    response = client.post(
        "/datasets/",
        headers=API_KEY,
        data={
            "dataset_name": "malformed_dataset",
            "description": "bad csv"
        },
        files={
            "file": ("bad.csv", file, "text/csv")
        }
    )

    assert response.status_code == 400