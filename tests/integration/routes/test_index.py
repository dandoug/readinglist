
def test_index_page(logged_in_client):
    response = logged_in_client.get("/")
    assert response.status_code == 200