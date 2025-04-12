from unittest.mock import MagicMock
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql import text

from app.services.about_service import _database_info


def test_database_info_postgresql(mocker):
    # Mock the db object and the engine connection
    mock_db = MagicMock()

    # Mock the engine and connection
    mock_engine = MagicMock(spec=Engine)  # Mock the Engine
    mock_connection = MagicMock(spec=Connection)  # Mock the connection
    mock_db.engine = mock_engine  # Mock engine on db object
    mock_connection.engine = mock_engine
    mock_engine.connect.return_value = mock_connection  # Mock connection from engine

    # Mock the dialect and assign a server_version_info for PostgreSQL
    mock_dialect = MagicMock()
    mock_dialect.server_version_info = (14, 2, 0)  # PostgreSQL version
    mock_connection.dialect = mock_dialect  # Attach mocked dialect to the connection

    # Mock the database type for PostgreSQL
    mock_engine.name = "postgresql"

    # Mock query execution results for PostgreSQL
    version_result = [("PostgreSQL 14.2",)]
    table_result = [("public", "my_table"), ("public", "another_table")]

    # Mock execute() method for version query and table schema query
    mock_connection.execute.side_effect = [
        MagicMock(fetchall=MagicMock(return_value=version_result)),  # For version query
        MagicMock(fetchall=MagicMock(return_value=table_result))  # For table query
    ]

    # Call the method under test
    result = _database_info(mock_db)
    print(result)  # Debugging line for visibility

    # Assertions to verify returned values
    assert "database_type" in result, "Key 'database_type' not found in result"
    assert "server_version" in result, "Key 'server_version' not found in result"
    assert result["database_type"] == "postgresql"
    assert result["server_version"] == "(14, 2, 0)"
    assert result["db_platform_info"] == ["('PostgreSQL 14.2',)"]
    assert result["db_table_info"] == [
        {"table_schema": "public", "table_name": "my_table"},
        {"table_schema": "public", "table_name": "another_table"}
    ]

    # Verify connection.close() was called
    mock_connection.close.assert_called_once()

def test_database_info_sqlite(mocker):
    # Mock the db object and engine connection
    mock_db = MagicMock()

    # Mock the engine and connection
    mock_engine = MagicMock(spec=Engine)  # Mock the Engine
    mock_connection = MagicMock(spec=Connection)  # Mock the connection
    mock_db.engine = mock_engine  # Attach mocked engine to db object
    mock_connection.engine = mock_engine
    mock_engine.connect.return_value = mock_connection  # Mock connection

    # SQLite does not support server_version_info, use a mock
    mock_dialect = MagicMock()
    mock_dialect.server_version_info = None  # SQLite-specific behavior
    mock_connection.dialect = mock_dialect  # Attach mocked dialect to connection

    # Mock the database type for SQLite
    mock_engine.name = "sqlite"

    # Mock query execution results for SQLite
    table_result = [["sqlite_table1"], ["sqlite_table2"]]

    # Mock execute() method for version query and table schema query
    mock_connection.execute.side_effect = [
        MagicMock(fetchall=MagicMock(return_value=table_result))  # For table query
    ]

    # Call the method under test
    result = _database_info(mock_db)
    print(result)  # Debugging line for visibility

    # Assertions to verify the returned values
    assert "database_type" in result, "Key 'database_type' not found in result"
    assert "server_version" in result, "Key 'server_version' not found in result"
    assert result["database_type"] == "sqlite"
    assert result["server_version"] == "None"  # SQLite doesn't have specific server version info
    assert result["db_table_info"] == [
        {"table_name": "sqlite_table1"},
        {"table_name": "sqlite_table2"}
    ]

    # Verify connection.close() was called
    mock_connection.close.assert_called_once()


def test_database_info_exception(mocker, caplog):
    # Mock the db object
    mock_db = MagicMock()

    # Mock the engine's `connect` method to raise an exception when called
    mock_engine = MagicMock(spec=Engine)
    mock_engine.connect.side_effect = Exception("Database connection failed")
    mock_db.engine = mock_engine

    # Call the method under test
    with caplog.at_level("ERROR"):  # Capture logging output at the ERROR level
        result = _database_info(mock_db)

    # Assertions for the returned result
    assert result == {}, "Expected an empty dictionary when an exception occurs"

    # Validate that the logging caught the correct error message
    assert any("Could not retrieve database info" in record.message for record in caplog.records), (
        "Did not log the expected error message"
    )

