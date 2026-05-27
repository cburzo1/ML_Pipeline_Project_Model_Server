API_KEY = {"x-api-key": "KEY123"}


def test_compare_nonexistent_models(client):

    response = client.post(
        "/metrics/",
        json={
            "model_ida": "fake-model-a",
            "model_idb": "fake-model-b"
        },
        headers=API_KEY
    )

    assert response.status_code == 404

    response_json = response.json()

    assert "detail" in response_json