import os
from urllib.parse import quote


def init_db(app):
    """
    Initializes the database connection for the application.

    This function sets up the connection to the database using the
    configuration parameters retrieved from environment variables.
    It configures the application with the necessary information for
    the SQLAlchemy database URI and disables SQLAlchemy modification tracking.
    The function also initializes the application with the SQLAlchemy
    database instance.

    :param app: The Flask application instance to configure the database for.
    :type app: Flask
    :return: None
    """
    host = os.getenv('RDS_HOSTNAME')
    port = os.getenv('RDS_PORT')
    db_name = os.getenv('RDS_DB_NAME')
    username = quote(os.getenv('RDS_USERNAME'))
    password = quote(os.getenv('RDS_PASSWORD'))

    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{username}:{password}@{host}:{port}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    from app import db
    db.init_app(app)
