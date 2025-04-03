import random
import string
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup


def test_details(logged_in_client):

    result = logged_in_client.get('/details')
    assert result.status_code == 400

    result = logged_in_client.get('/details', query_string={'id': 500})
    assert result.status_code == 404

    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200

    book = result.json
    assert book is not None
    assert book['id'] == 355
    assert book['title'] == 'Reacher Said Nothing: Lee Child and the Making of Make Me'
    assert book['asin'] == '1509540857'
    assert book['rating'] == 4.0
    assert book['author'] == 'Andy Martin'

    result = logged_in_client.get('/library_searches', query_string={'title': book['title']})
    assert result.status_code == 400

    result = logged_in_client.get('/library_searches', query_string={'author': book['author'], 'title': book['title']})
    assert result.status_code == 200
    searches = result.json
    assert searches is not None
    assert len(searches) >= 6
    assert "Santa Clara Country Library" in searches
    assert urlparse(searches["Santa Clara Country Library"]).netloc == 'sccl.bibliocommons.com'


def test_edit(logged_in_client, client):

    result = client.get('edit_book', query_string={'id': 355})
    assert result.status_code == 403

    result = logged_in_client.get('edit_book', query_string={'id': 355})
    assert result.status_code == 200

    soup = BeautifulSoup(result.data, 'html.parser')

    _check_form_element(soup, 'id', '355')
    _check_form_element(soup, 'title', 'Reacher Said Nothing: Lee Child and the Making of Make Me')
    _check_form_element(soup, 'asin', '1509540857')
    _check_form_element(soup, 'rating', '4.0')
    _check_form_element(soup, 'author', 'Andy Martin')

    form_params = {input_element['id']: input_element['value'] for input_element in
                   soup.find_all('input', {'id': True, 'value': True})}
    form_params['submit'] = 'Update Book'
    form_params['next'] = "/some_special_place?go=ok"
    # update hardcover to something new
    form_params['hardcover'] = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    result = logged_in_client.post('edit_book', data=form_params)
    assert result.status_code == 302
    assert result.headers["Location"].endswith(form_params['next'])

    # get the details back and check that hardcover was updated
    result = logged_in_client.get('details', query_string={'id': 355})
    assert result.status_code == 200
    book = result.json
    assert book is not None
    assert book['hardcover'] == form_params['hardcover']


def test_add_delete(logged_in_client, client):
    result = client.get('add_book')
    assert result.status_code == 403

    result = logged_in_client.get('add_book')
    assert result.status_code == 200

    soup = BeautifulSoup(result.data, 'html.parser')

    # Build form data for new book
    form_params = {}
    form_params['csrf_token'] = soup.find("input", {"id": "csrf_token"})["value"]
    form_params['next'] = "/some_special_place?go=ok"

    # get details for book we are copying
    result = logged_in_client.get('/details', query_string={'id': 355})
    assert result.status_code == 200

    book = result.json
    assert book is not None
    attributes = ['asin', 'author', 'bestsellers_rank_flat', 'categories_flat', 'image',
                  'isbn_10', 'isbn_13', 'link', 'rating', 'specifications_flat',
                  'status', 'title']
    for attr in attributes:
        form_params[attr] = book[attr]

    result = logged_in_client.post('add_book', data=form_params)
    assert result.status_code == 302
    assert result.headers["Location"].endswith(form_params['next'])

    # Access and assert flash messages from the session
    with logged_in_client.session_transaction() as session:
        flash_messages = session.get('_flashes', [])
        assert len(flash_messages) == 1
        category, message = flash_messages[0]
        assert category == 'success'
        match = re.search(r"Book id:(\d+) title:'(.*)' added successfully\!", message)
        assert match is not None
        added_book_id = int(match.group(1))
        session['_flashes'] = [] # clear flashes so the delete will be only message

    delete_params = {'book_id': added_book_id}

    result = client.post('delete_book', data=delete_params)
    assert result.status_code == 403

    result = logged_in_client.post('delete_book', data=delete_params)
    assert result.status_code == 200
    with logged_in_client.session_transaction() as session:
        flash_messages = session.get('_flashes', [])
        assert len(flash_messages) == 1
        category, message = flash_messages[0]
        assert category == 'success'
        match = re.search(r"Book id:(\d+) deleted successfully\!", message)
        assert match is not None
        deleted_book_id = int(match.group(1))
        assert deleted_book_id == added_book_id


def _check_form_element(soup: BeautifulSoup, element_id: str, element_value: str):
    input_element = soup.find("input", {"id": element_id})
    assert input_element is not None
    assert input_element["value"] == element_value

