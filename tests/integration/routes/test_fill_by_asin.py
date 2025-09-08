

def test_file_by_asin(logged_in_client, asin_data_service):
    response = logged_in_client.get('/fill_by_asin')
    assert response.status_code == 400

    response = logged_in_client.get('/fill_by_asin', query_string={'asin': '0'})
    assert response.status_code == 400

    #response = logged_in_client.get('/fill_by_asin', query_string={'asin': 'Z1A2B3C4D5'})
    #assert response.status_code == 404

    response = logged_in_client.get('/fill_by_asin', query_string={'asin': '1509540857'})
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data is not None

    assert response_data['asin'] == '1509540857'
    assert response_data['author'] == 'Andy Martin'
    assert response_data['isbn_10'] == '1509540857'
    assert response_data['isbn_13'] == '978-1509540853'
    assert (response_data['link'] ==
            'https://www.amazon.com/Reacher-Said-Nothing-Child-Making/dp/1509540857')
    assert response_data['title'] == 'Reacher Said Nothing: Lee Child and the Making of Make Me'
