
def test_status(client, logged_in_client):
    params = {'book_id': 'x355'}

    result = client.post('/change_status', data=params)
    assert result.status_code == 302  # not logged in
    assert "/login" in result.headers["Location"]

    result = logged_in_client.post('/change_status', data=params)
    assert result.status_code == 400  # bad book id

    params = {'book_id': '355'}

    result = logged_in_client.post('/change_status', data=params)
    assert result.status_code == 400  # missing status

    params['status'] = 'xread'
    result = logged_in_client.post('/change_status', data=params)
    assert result.status_code == 400  # bad status

    params['status'] = 'read'
    result = logged_in_client.post('/change_status', data=params)
    assert result.status_code == 200

    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200
    book = result.json
    assert book is not None
    assert book['status'] == 'read'

    params['status'] = 'up_next'
    result = logged_in_client.post('/change_status', data=params)
    assert result.status_code == 200

    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200
    book = result.json
    assert book is not None
    assert book['status'] == 'up_next'

    params['status'] = 'none'
    result = logged_in_client.post('/change_status', data=params)
    assert result.status_code == 200

    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200
    book = result.json
    assert book is not None
    assert book['status'] == 'none'


def test_feedback(client, logged_in_client):
    params = {'book_id': 'x355'}

    result = client.post('/change_feedback', data=params)
    assert result.status_code == 302  # not logged in
    assert "/login" in result.headers["Location"]

    result = logged_in_client.post('/change_feedback', data=params)
    assert result.status_code == 400  # bad book id

    params = {'book_id': '355'}

    result = logged_in_client.post('/change_feedback', data=params)
    assert result.status_code == 400  # missing feedbacj

    params['feedback'] = 'xlike'
    result = logged_in_client.post('/change_feedback', data=params)
    assert result.status_code == 400  # bad feedback

    params['feedback'] = 'like'
    result = logged_in_client.post('/change_feedback', data=params)
    assert result.status_code == 200

    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200
    book = result.json
    assert book is not None
    assert book['feedback'] == 'like'

    params['feedback'] = 'dislike'
    result = logged_in_client.post('/change_feedback', data=params)
    assert result.status_code == 200

    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200
    book = result.json
    assert book is not None
    assert book['feedback'] == 'dislike'

    params['feedback'] = 'none'
    result = logged_in_client.post('/change_feedback', data=params)
    assert result.status_code == 200

    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200
    book = result.json
    assert book is not None
    assert book['feedback'] == 'none'

