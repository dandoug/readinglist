import os
import logging
from datetime import datetime, timezone

from flask import Flask
from flask_admin import Admin
from flask_caching import Cache
from flask_login import user_logged_out
from flask_mailman import Mail
from flask_security import SQLAlchemyUserDatastore, Security, hash_password
from flask_sqlalchemy import SQLAlchemy

from app.config import configure_app_logging
from app.helpers import register_globals

# Initial admin user.  Only create if db contains no admins
INITIAL_USER_PASSWORD = "example1"
INITIAL_USER_EMAIL    = "admin@example.com"

db = SQLAlchemy()
user_datastore = None
admin = None
cache = None


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

    # Set up logging for the environment
    configure_app_logging(env)

    # Set up email handling using Flask-Mailman using context info
    mail = Mail(app)

    # Setup Flask-Security
    from app.security import User, Role
    global user_datastore
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    db.init_app(app)
    mail.init_app(app)

    # Initialize the Admin object
    from app.security import SecureAdminIndexView
    global admin
    admin = Admin(app, name='Book List Administration', template_mode='bootstrap4',
                  index_view=SecureAdminIndexView(name="Admin"))

    # Lazily init data models with their relationships
    from app.models import ReadingStatus, Feedback, Book
    from app.security import User

    # override the user loader for login manager to use some caching to reduce database loads of user/roles
    from app.security import custom_user_loader, on_logout
    security.login_manager.user_loader(custom_user_loader)
    user_logged_out.connect(on_logout, app)  # invalidate cache entry on logout

    # setup of users and roles, will bootstrap database with basic requirements if necessary
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
                confirmed_at=datetime.now().astimezone(timezone.utc), # obviates need to confirm this email
                password=hash_password(INITIAL_USER_PASSWORD),
                roles=["admin"])
        db.session.commit()

    # Import routes
    with app.app_context():
        register_globals(app)

        global cache
        cache = Cache(app)

        from . import routes

        from app.security import registration_bp
        app.register_blueprint(registration_bp)

        from app.security import register_admin_views
        register_admin_views(db, admin)

    from app.helpers import render_icon
    app.jinja_env.filters['render_icon'] = render_icon

    return app
