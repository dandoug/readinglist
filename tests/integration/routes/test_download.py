import csv
import io

from flask import Response


def test_author_download(client):
    response = client.get('/download', query_string={'author': 'rand'})
    assert response.status_code == 200

    data = _receive_csv_file(response)

    assert len(data) == 3

    response = client.get('/download', query_string={'author': 'rand', 'sortColumn': 'description'})
    assert response.status_code == 400
    response = client.get('/download', query_string={'author': 'rand', 'sortColumn': 'author', 'sortOrder': 'x'})
    assert response.status_code == 400

    response = client.get('/download', query_string={'author': 'rand', 'sortColumn': 'author', 'sortOrder': 'desc'})
    assert response.status_code == 200
    data = _receive_csv_file(response)
    assert len(data) == 3
    bk = data[0]
    assert bk['Author'] == 'Laura Hillenbrand'


def test_title_download(client):
    response = client.get('/download', query_string={'title': 'war'})
    assert response.status_code == 200

    data = _receive_csv_file(response)

    assert len(data) == 57

    response = client.get('/download', query_string={'title': 'war', 'sortColumn': 'title', 'sortOrder': 'asc'})
    assert response.status_code == 200
    data = _receive_csv_file(response)
    assert len(data) == 57
    bk = data[0]
    assert bk['Title'] == 'A Higher Form of Killing: The Secret History of Chemical and Biological Warfare'


def test_category_download(client):
    response = client.get('/download', query_string={'cat': ['Q2xhc3NpY3M*', 'RmFudGFzeQ**']})
    assert response.status_code == 200

    data = _receive_csv_file(response)

    assert len(data) == 3

    response = client.get('/download', query_string={'cat': ['Q2xhc3NpY3M*', 'RmFudGFzeQ**'], 'sortColumn': 'rating', 'sortOrder': 'desc'})
    assert response.status_code == 200
    data = _receive_csv_file(response)
    assert len(data) == 3
    bk = data[0]
    assert bk['Title'] == 'The Hobbit: 75th Anniversary Edition'


def test_all_books(client):
    response = client.get('/download', query_string={'author': '*'})
    assert response.status_code == 200

    data = _receive_csv_file(response)

    assert len(data) == 200


def test_no_results(client):
    response = client.get('/download', query_string={'author': 'warx'})
    assert response.status_code == 200

    data = _receive_csv_file(response)

    assert len(data) == 0


def test_bad_args(client):
    response = client.get('/download')
    assert response.status_code == 400

    response = client.get('/download', query_string={'authorx': 'warx'})
    assert response.status_code == 400


def test_one_results(client):
    response = client.get('/download', query_string={'cat': 'Q3JpdGljaXNtID4gRXVyb3BlYW4*'})
    assert response.status_code == 200

    data = _receive_csv_file(response)

    assert len(data) == 1
    row = data[0]
    assert row['Title']  == "Reacher Said Nothing: Lee Child and the Making of Make Me"


def _receive_csv_file(resp: Response):
    assert resp.mimetype == 'text/csv'
    # Decode the binary response data to a string
    csv_content = resp.data.decode('utf-8')
    # Create a file-like object from the CSV string
    csv_file = io.StringIO(csv_content)
    # Use csv.DictReader to parse the CSV into a list of dictionaries
    csv_reader = csv.DictReader(csv_file)
    # Convert the reader object to a list of dictionaries
    return list(csv_reader)
