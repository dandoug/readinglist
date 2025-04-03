import pytest
from unittest.mock import Mock
from flask import Flask
from app.helpers import compute_next_url


@pytest.fixture
def app():
    # Create a Flask app for testing
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Add a dummy "index" route
    @app.route("/")
    def index():
        return "Index Page"

    return app


def test_compute_next_url_no_referrer(app):
    with app.test_request_context():
        mock_request = Mock()
        mock_request.referrer = None  # Simulate no referrer
        assert compute_next_url(mock_request) == '/'


def test_compute_next_url_with_referrer_no_query(app):
    with app.test_request_context():
        URL = "http://booklist.media/search"
        mock_request = Mock()
        mock_request.referrer = URL
        assert compute_next_url(mock_request) == URL[URL.rfind('/'):]


def test_compute_next_url_with_referrer_and_query(app):
    with app.test_request_context():
        URL = "http://booklist.media/search?cat=Q3JpdGljaXNtID4gRXVyb3BlYW4*&cat=Q3JpdGljaXNtID4gRm9sayBUYWxlcw**"
        mock_request = Mock()
        mock_request.referrer = URL  # URL with query string
        assert compute_next_url(mock_request) == URL[URL.rfind('/'):]
