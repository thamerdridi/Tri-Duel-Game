"""Test health endpoint."""


def test_health_check(client):
    """Test that health endpoint returns OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
