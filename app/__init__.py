import os
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask
from flask_admin import Admin
from flask_mailman import Mail
from flask_security import SQLAlchemyUserDatastore, Security, hash_password
from flask_sqlalchemy import SQLAlchemy

# Initial admin user.  Only create if db contains no admins
INITIAL_USER_PASSWORD = "example1"
INITIAL_USER_EMAIL    = "admin@example.com"

load_dotenv()  # Loads variables from .env into the environment if file exists

db = SQLAlchemy()
user_datastore = None
admin = None


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

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Set up email handling using Flask-Mailman
    mail = Mail(app)  # Initialize Flask-Mailman

    # Setup Flask-Security
    from app.security.models import User, Role
    global user_datastore
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore) # overridden below

    db.init_app(app)
    mail.init_app(app)

    # Initialize the Admin object
    from app.security.secure_index_view import SecureAdminIndexView
    global admin
    admin = Admin(app, name='Book List Administration', template_mode='bootstrap4',
                  index_view=SecureAdminIndexView(name="Admin"))

    # setup of users and roles
    with app.app_context():
        security.datastore.find_or_create_role(name='admin', description='Administrator')
        security.datastore.find_or_create_role(name='editor', description='Editor')

        # Count the number of users with the 'admin' role
        admin_role = security.datastore.find_role('admin')
        admin_count = len(admin_role.users.all()) if admin_role else 0

        # Create initial user if there are no other admins
        if admin_count == 0:
            logging.warning(f"Creating default admin user, {INITIAL_USER_EMAIL}")
            security.datastore.create_user(
                email=INITIAL_USER_EMAIL,
                confirmed_at=datetime.now().astimezone(timezone.utc),
                password=hash_password(INITIAL_USER_PASSWORD),
                roles=["admin"])
        db.session.commit()

    # Import routes
    with app.app_context():
        from . import routes
        from .security import routes

    return app
