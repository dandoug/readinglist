

def test_about_page(logged_in_client):
    response = logged_in_client.get("/about")
    assert response.status_code == 200
