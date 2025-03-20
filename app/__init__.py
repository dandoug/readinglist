import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.routes import register_routes
from app.database import init_db


load_dotenv()  # Loads variables from .env into the environment if file exists

db = SQLAlchemy()


def create_app():
    """
    Creates and configures the Flask application instance. This function is
    responsible for creating the application, registering necessary routes,
    and returning the configured Flask app, ready to be run.

    :return: Flask application instance.
    :rtype: Flask
    """

    app = Flask(__name__, template_folder="templates", static_folder="static")
    # Load config by environment
    env = os.getenv("FLASK_ENV", "development")  # Default to "development"
    app.config.from_object(f"app.config.{env.capitalize()}Config")

    init_db(app)

    # Register the routes
    register_routes(app)
    return app


