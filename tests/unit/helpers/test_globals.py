import pytest
from flask import Flask, abort, render_template_string, g
from unittest.mock import Mock

from app.helpers.globals import register_globals

TEST_URL = 'https://booklist.media/search?cat=Q3JpdGljaXNtID4gRXVyb3BlYW4*&cat=Q3JpdGljaXNtID4gRm9sayBUYWxlcw**'


@pytest.fixture
def app():
    """Creates and configures a test Flask app."""
    app = Flask(__name__)
    register_globals(app)
    return app


@pytest.fixture
def mock_current_user():
    mock_current_user = Mock()
    mock_current_user.is_authenticated = True  # Mock user to simulate an authenticated session
    return mock_current_user


def test_403_error_handler(app):
    """Test that the 403 error handler is properly registered and responds correctly."""
    with app.test_client() as client:
        # Simulate raising a 403 error in the app.
        @app.route('/forbidden')
        def forbidden():
            abort(403)

        response = client.get('/forbidden')  # This should trigger the 403 error handler.
        assert response.status_code == 403
        response_json = response.get_json()
        assert 'error' in response_json
        assert response_json['error'].startswith('You do not have permission to access this resource')


def test_context_processor(app):
    """Test that the parse_url helper is registered in the Jinja2 context."""
    with app.test_client() as client:
        # Simulate raising a 403 error in the app.
        @app.route('/parseit')
        def parseit():
            return render_template_string("{{ parse_url('https://booklist.media/search?cat=Q3JpdGljaXNtID4gRXVyb3BlYW4*&cat=Q3JpdGljaXNtID4gRm9sayBUYWxlcw**').query|safe }}")

        response = client.get('/parseit')  # Test the parse_url helper in template processing
        assert response.status_code == 200
        response_str = response.get_data(as_text=True)
        assert response_str == 'cat=Q3JpdGljaXNtID4gRXVyb3BlYW4*&cat=Q3JpdGljaXNtID4gRm9sayBUYWxlcw**'


# @patch('globals.current_user', new_callable=MagicMock)
def test_global_jinja_vars(mock_current_user, app):
    """Test that current_user is added to the global Jinja environment before each request."""

    with app.test_client() as client:
        # Simulate raising a 403 error in the app.
        @app.route('/')
        def index():
            # This sets in local context, but the add_global_vars() call we registered will copy to global
            g._login_user = mock_current_user
            # Macro access of current_user fails unless current_user set in globals causing this
            # template string to fail because current_user is unknown in macro's context
            return render_template_string("""
                {%- macro user_is_authenticated() -%}
                    {{ current_user.is_authenticated }}
                {%- endmacro -%}
                Current user authenticated: {{ user_is_authenticated() }}""")

        # Make a simple request to trigger the before_request function
        response = client.get('/')

        # Check that the current_user is available in the Jinja global environment
        assert response.status_code == 200  # if current_user is unknown to macro, will get 500 here
        response_str = response.get_data(as_text=True)
        assert response_str == 'Current user authenticated: True'
