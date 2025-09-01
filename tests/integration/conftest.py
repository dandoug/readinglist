import os
import subprocess
import time

import pytest
import pymysql
import smtplib
import poplib
from pathlib import Path
from threading import Thread
from flask import Flask, jsonify, request
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import app
from app import create_app
from tests.integration.sql_parser.parser import SQLParser

# Calculate the path to where the SQL files are
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # Navigate to the project root
DATABASE_DIR = PROJECT_ROOT / "database"
INTEGRATION_DIR = PROJECT_ROOT / "tests" / "integration"


@pytest.fixture(scope="session")
def docker_compose():
    """Start the Docker Compose services."""
    compose_file = INTEGRATION_DIR / "docker-compose.yml"

    try:
        # Start services and wait for health checks to pass
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "up", "-d", "--wait", "--wait-timeout", "300"],
            check=True
        )
        yield
    finally:
        # Tear down services
        subprocess.run(["docker", "compose",  "-f", str(compose_file), "down"], check=True)


@pytest.fixture(scope="session")
def db_connection(docker_compose):
    """Provide a connection to the MySQL test database."""

    # Work around for running in container under act (https://github.com/nektos/act)
    if os.getenv("ACT") and os.getenv("RDS_HOSTNAME") == "localhost":
        DB_HOST = "host.docker.internal"
    else:
        DB_HOST = os.getenv("RDS_HOSTNAME")

    DB_PORT = int(os.getenv("RDS_PORT", "13306"))

    # Retry with exponential backoff up to a deadline (default 120s)
    deadline_seconds = int(os.getenv("DB_CONNECT_DEADLINE_SECONDS", "90"))
    per_attempt_timeout = int(os.getenv("DB_CONNECT_TIMEOUT_SECONDS", "3"))
    backoff_sequence = [0.5, 1, 2, 3, 5, 8, 13, 21, 34]  # seconds

    start = time.monotonic()
    last_err = None

    for delay in backoff_sequence + [5] * 50:  # keep trying with 5s after sequence until deadline
        try:
            print(f"Connecting to database at {DB_HOST}:{DB_PORT}...")
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user="test_user",
                password="test_password",
                database="test_readinglist",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=per_attempt_timeout,
            )
            # Optional: simple sanity query to ensure server is fully ready
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            yield conn
            conn.close()
            break
        except pymysql.err.OperationalError as e:
            last_err = e
            if time.monotonic() - start >= deadline_seconds:
                break
            print(f"Failed to connect to the database: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    else:
        pass  # kept for structure; loop 'break' exits earlier

    if last_err:
        pytest.fail(f"Failed to connect to the database within {deadline_seconds}s: {last_err}")



@pytest.fixture(scope="session")
def smtp_connection(docker_compose):
    """Provide a connection to the SMTP server."""
    # Work around for running in container under act (https://github.com/nektos/act)
    if os.getenv("ACT") and os.getenv("MAIL_SERVER") == "localhost":
        SMTP_HOST = "host.docker.internal"
    else:
        SMTP_HOST = os.getenv("MAIL_SERVER")
    try:
        conn = smtplib.SMTP(host=SMTP_HOST, port=1025)
        yield conn
        conn.quit()
    except Exception as e:
        pytest.fail(f"Failed to connect to the SMTP server: {e}")


@pytest.fixture(scope="session")
def pop_connection(docker_compose):
    """Provide a connection to the POP3 server."""
    if os.getenv("ACT") and os.getenv("MAIL_SERVER") == "localhost":
        POP_HOST = "host.docker.internal"
    else:
        POP_HOST = os.getenv("MAIL_SERVER")
    try:
        conn = poplib.POP3(host=POP_HOST, port=1100)
        yield conn
        conn.quit()
    except Exception as e:
        pytest.fail(f"Failed to connect to the POP3 server: {e}")


@pytest.fixture(scope="session", autouse=True)
def load_initial_data(db_connection):
    """
    Load test data from the SQL script 
    """
    TABLE_SCRIPTS = [
        "create-tables.sql",
        "initial-books-load.sql"
    ]
    for script_name in TABLE_SCRIPTS:
        sql_file_path = DATABASE_DIR / script_name
        execute_sql_file(db_connection, sql_file_path)


@pytest.fixture(scope="session")
def flask_app(db_connection, smtp_connection):
    """
    Create a Flask application fixture that depends on the database and SMTP server.
    Runs once per test session.
    """
    # Create the application
    app = create_app()

    # The app created a user with email=app.INITIAL_USER_EMAIL that
    # has the admin role.  For testing purposes, we add the `editor` role to
    # that user here, too
    with app.app_context():
        from app import user_datastore, INITIAL_USER_EMAIL, db
        user = user_datastore.find_user(email=INITIAL_USER_EMAIL)
        user_datastore.add_role_to_user(user, 'editor')
        db.session.commit()

    yield app


@pytest.fixture(scope="session")
def asin_data_service(flask_app):
    """
    Create a second Flask application listening on port 8008.
    This app sends back default test data for requests.
    
    Sample request URL:
    https://api.asindataapi.com/request?api_key=...key...&amazon_domain=amazon.com&asin=1509540857&type=product
    
    Response in file asin_service_response.json
    """

    # Get host and port for test data provider
    test_url = flask_app.config['ASIN_DATA_API_URL']
    parsed_url = urlparse(test_url)
    asin_host = parsed_url.hostname
    asin_port = parsed_url.port

    asin_app = Flask(__name__)

    # Read in the sample response data as a dictionary
    file_path = Path(__file__).parent / "asin_sample_response.json"
    with open(file_path, "r", encoding='utf-8') as file:
        json_data = json.load(file)

    @asin_app.route('/request', methods=['GET'])
    def stub_request():
        asin = request.args.get("asin", None)
        if asin == '0':
            return jsonify({})
        return jsonify(json_data)

    # Run the app in a separate thread
    def run_app():
        asin_app.run(host=asin_host, port=asin_port)

    thread = Thread(target=run_app, daemon=True)
    thread.start()

    yield app  # Provide the app for the fixture lifecycle



@pytest.fixture
def client(flask_app):
    """
    Create a test client using the Flask app for individual tests.
    """
    return flask_app.test_client()


@pytest.fixture
def logged_in_client(flask_app):
    client = flask_app.test_client()
    response = client.get('/login')
    assert response.status_code == 200

    # Parse the CSRF token from the response HTML
    soup = BeautifulSoup(response.data, "html.parser")
    csrf_token = soup.find("input", {"id": "csrf_token"})["value"]

    # Log in to create a session 
    form_params = {
        "next": "/",
        "csrf_token": csrf_token,
        "email": app.INITIAL_USER_EMAIL,
        "password": app.INITIAL_USER_PASSWORD,
        "submit": "Login"
    }
    response = client.post('/login', data=form_params)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    return client


def execute_sql_file(db_session, file_path):
    """
    Execute SQL commands from a file against the given database session.

    Args:
        db_session: PyMySQL connection object.
        file_path: Path to the SQL script file.
    """
    assert file_path.exists()

    print(f"\n\nParsing {file_path}...")
    parser = SQLParser(file_path)
    assert parser.has_errors() is False

    with db_session.cursor() as cursor:  # Use a cursor from the connection
        # Execute SQL script
        for statement in parser.statements():
            cursor.execute(statement)

    db_session.commit()  # Remember to commit changes
