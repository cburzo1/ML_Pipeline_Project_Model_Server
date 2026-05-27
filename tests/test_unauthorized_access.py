def test_missing_api_key(client):

    response = client.get("/datasets/")

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid or missing API key"
    }


def test_invalid_api_key(client):

    response = client.get(
        "/datasets/",
        headers={
            "x-api-key": "INVALID_KEY"
        }
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid or missing API key"
    }