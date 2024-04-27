def test_admin_landing(client):
    response = client.get("/")
    assert response.status_code == 200