from bs4 import BeautifulSoup
import re


def test_author_search(client):
    response = client.get('/search', query_string={'author': 'rand'})
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    verify_number_of_results(soup, 3)


def test_title_search(client):
    response = client.get('/search', query_string={'title': 'war'})
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    verify_number_of_results(soup, 57)

def test_category_search(client):
    response = client.get('/search', query_string={'cat': ['Q2xhc3NpY3M*','RmFudGFzeQ**']})
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    verify_number_of_results(soup, 3)

def test_all_books(client):
    response = client.get('/search', query_string={'author': '*'})
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    verify_number_of_results(soup, 200)

def test_no_results(client):
    response = client.get('/search', query_string={'author': 'warx'})
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    verify_number_of_results(soup, 0)

def test_bad_args(client):
    response = client.get('/search')
    assert response.status_code == 400

    response = client.get('/search', query_string={'authorx': 'warx'})
    assert response.status_code == 400


def test_one_results(client):
    response = client.get('/search', query_string={'cat': 'Q3JpdGljaXNtID4gRXVyb3BlYW4*'})
    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    verify_number_of_results(soup, 1)

    tr = soup.find("tr", {"data-id": "355"})
    assert tr is not None
    title_text = tr.find("span").get_text() if tr else None
    assert title_text == "Reacher Said Nothing: Lee Child and the Making of Make Me"


def verify_number_of_results(soup, expected_number_of_results):
    # Get the results summary line
    summary_line = soup.find("span", {"id": "search-results-summary"}).get_text()

    if expected_number_of_results == 0:
        match =  re.search(r"No matching books were found\.", summary_line)
        number_of_matched_books = 0 if match else None
    elif expected_number_of_results == 1:
        match = re.search(r"Found a matching book\.", summary_line)
        number_of_matched_books = 1 if match else None
    else:
        match = re.search(r"Found (\d+) matching books\.", summary_line)
        number_of_matched_books = int(match.group(1)) if match else None

    assert match is not None, "Summary line did not match the expected format."
    assert number_of_matched_books == expected_number_of_results


