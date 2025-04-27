"""
Flask application factory module responsible for creating and configuring the application 
instance.

This module initializes core Flask extensions, sets up security, configures logging, and manages 
db connections. It handles user authentication, admin interface setup, and asset bundling for 
the application. The module provides a create_app() factory function that returns a fully 
configured Flask application instance ready for deployment.
"""
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
from flask_assets import Bundle, Environment

from app.config import configure_app_logging, PROJECT_ROOT
from app.helpers import register_globals

# Initial admin user.  Only create if db contains no admins
INITIAL_USER_PASSWORD = "example1"  # nosec B105, noqa: dodgy:password
INITIAL_USER_EMAIL    = "admin@example.com"

db = SQLAlchemy()
user_datastore = None  # pylint: disable=invalid-name
admin = None  # pylint: disable=invalid-name
cache = None  # pylint: disable=invalid-name`


# pylint: disable=too-many-locals
def create_app():
    """
    Creates and configures the Flask application instance. This function is
    responsible for creating the application, registering the necessary routes,
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
    from app.security import User, Role  # pylint: disable=import-outside-toplevel
    global user_datastore  # pylint: disable=global-statement
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)

    db.init_app(app)
    mail.init_app(app)

    # Initialize the Admin object
    from app.security import SecureAdminIndexView  # pylint: disable=import-outside-toplevel
    global admin  # pylint: disable=global-statement
    admin = Admin(app, name='Book List Administration', template_mode='bootstrap4',
                  index_view=SecureAdminIndexView(name="Admin"))

    # Lazily init data models with their relationships
    from app.models import ReadingStatus, Feedback, Book  # pylint: disable=import-outside-toplevel,unused-import

    # override the user loader for login manager to reduce database loads of user/roles
    from app.security import custom_user_loader, on_logout  # pylint: disable=import-outside-toplevel
    security.login_manager.user_loader(custom_user_loader)
    user_logged_out.connect(on_logout, app)  # invalidate cache entry on logout

    # setup of users and roles will bootstrap the database with basic requirements if necessary
    with app.app_context():
        security.datastore.find_or_create_role(name='admin', description='Administrator')
        security.datastore.find_or_create_role(name='editor', description='Editor')

        # Count the number of users with the 'admin' role
        admin_role = security.datastore.find_role('admin')
        admin_count = len(admin_role.users.all()) if admin_role else 0

        # Create an initial user if there are no other admins
        if admin_count == 0:
            logging.warning("Creating default admin user, %s", INITIAL_USER_EMAIL)
            security.datastore.create_user(
                email=INITIAL_USER_EMAIL,
                confirmed_at=datetime.now().astimezone(timezone.utc),  # skip confirmation
                password=hash_password(INITIAL_USER_PASSWORD),
                roles=["admin"])
        db.session.commit()

    # Import routes
    with app.app_context():
        register_globals(app)

        global cache  # pylint: disable=global-statement
        cache = Cache(app)

        # noinspection PyUnresolvedReferences
        from app import routes  # pylint: disable=import-outside-toplevel,unused-import

        from app.security import registration_bp  # pylint: disable=import-outside-toplevel
        app.register_blueprint(registration_bp)

        from app.security import register_admin_views  # pylint: disable=import-outside-toplevel
        register_admin_views(db, admin)

    from app.helpers import render_icon  # pylint: disable=import-outside-toplevel
    app.jinja_env.filters['render_icon'] = render_icon

    # Define your SCSS file bundle
    output_dir = PROJECT_ROOT / "app" / "static" / "gen" / "css"
    os.makedirs(output_dir, exist_ok=True)
    scss = Bundle(
        'scss/badge-color.scss',
        filters='libsass',
        output='gen/css/badge-color.css'  # Compiled CSS file location
    )

    assets = Environment(app)
    assets.register('badge-color', scss)

    # Build assets during app initialization
    # Programmatically build assets during application startup
    with app.app_context():
        # noinspection PyProtectedMember
        for name, bundle in assets._named_bundles.items():  # pylint: disable=protected-access
            logging.info("Building asset bundle: %s", name)
            bundle.build(force=True)  # The `force=True` ensures the bundle rebuilds every time

    return app
