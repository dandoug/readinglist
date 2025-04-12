"""
This module provides functionality to gather and expose metadata about the application, 
its runtime environment, and its database status. It is responsible for reading build 
information, inspecting installed libraries, and fetching database details (e.g., type, 
version, and tables). The module ensures important environment variables are securely 
exposed and includes necessary initialization steps.
"""
import logging
import os
import platform
import sys
from importlib.metadata import distributions

from sqlalchemy import text

from app.config import PROJECT_ROOT
from app.helpers import check_and_generate_build_info, read_build_info

# during application initialization, make sure the build_info file is current
check_and_generate_build_info()


def build_about_info() -> dict:
    """
    Generate a dictionary containing detailed information about the application environment,
    system, Python runtime, libraries, and database.

    This function collects a comprehensive set of data about the runtime environment
    of the application. This includes system details, Python interpreter information,
    installed libraries with their respective metadata, safe environment variables,
    and database statistics. The collected data is consolidated into a dictionary, which
    can be used for debugging, logging, or display purposes.

    :returns: A dictionary containing detailed build and environment information.
    :rtype: dict
    """
    about_info = read_build_info()

    about_info["python_version"] = sys.version
    about_info["platform"] = sys.platform
    about_info["app_filepath"] = os.path.abspath(PROJECT_ROOT)
    about_info["installed_libraries"] = [
        {"name": dist.metadata["Name"], "version": dist.version,
         "homepage": dist.metadata["Home-Page"] if "Home-Page" in dist.metadata else "N/A"}
        for dist in distributions()]
    about_info["environment"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_implementation": platform.python_implementation(),
        "python_compiler": platform.python_compiler(),
    }
    about_info["vars"] = _get_safe_environment_variables()
    from app import db # pylint: disable=import-outside-toplevel
    about_info["database"] = _database_info(db)

    return about_info


def _get_safe_environment_variables():
    # List of environment variables to expose (whitelist)
    allowed_env_vars = ["FLASK_ENV", "RDS_HOSTNAME", "RDS_PORT", "RDS_DB_NAME",
                        "MAIL_SERVER", "MAIL_PORT", "SECURITY_EMAIL_SENDER"]

    # Filter and return only the allowed variables
    return {key: os.environ.get(key) for key in allowed_env_vars if key in os.environ}


def _database_info(db):
    """Expose basic database info such as type and version."""
    try:
        # Establish a raw connection to extract database info
        connection = db.engine.connect()
        server_version = connection.dialect.server_version_info
        database_type = connection.engine.name

        query = None
        table_query = None
        # Define database-specific queries
        if database_type == "postgresql":
            query = text("SELECT version();")
            table_query = text("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_type = 'BASE TABLE' 
                AND table_schema NOT IN ('pg_catalog', 'information_schema');
            """)
        elif database_type == "mysql":
            query = text("SHOW VARIABLES LIKE '%os%';")
            table_query = text("SHOW TABLES;")
        elif database_type == "sqlite":
            # noinspection SqlResolve
            table_query = text("SELECT name FROM sqlite_master WHERE type='table';")



        db_platform_info = None
        if query is not None:
            result = connection.execute(query).fetchall()
            db_platform_info = [str(row) for row in result]

        db_table_info = None
        if table_query is not None:
            result = connection.execute(table_query).fetchall()
            # Convert rows properly depending on their structure
            if database_type == "postgresql":
                db_table_info = [{"table_schema": row[0], "table_name": row[1]} for row in result]
            elif database_type == "mysql":
                db_table_info = [{"table_name": row[0]} for row in result]
            elif database_type == "sqlite":
                db_table_info = [{"table_name": row[0]} for row in result]

        connection.close()

        return {
            "database_type": database_type,
            "server_version": f"{server_version}",
            "db_platform_info": db_platform_info if db_platform_info else "",
            "db_table_info": db_table_info if db_table_info else ""
        }
    except Exception as e: # pylint: disable=broad-except
        logging.error("Could not retrieve database info: %s", e, exc_info=True)
        return {}


__all__ = ["build_about_info"]
