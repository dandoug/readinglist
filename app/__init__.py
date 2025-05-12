"""
Flask application factory module responsible for creating and configuring the application 
instance.

This module initializes core Flask extensions, sets up security, configures logging, and manages 
db connections. It handles user authentication, admin interface setup, and asset bundling for 
the application. The module provides a create_app() factory function that returns a fully 
configured Flask application instance ready for deployment.
"""
import logging
import os
from datetime import datetime, timezone

from flask import Flask
from flask_admin import Admin
from flask_assets import Bundle, Environment
from flask_caching import Cache
from flask_limiter.util import get_remote_address
from flask_login import user_logged_out
from flask_mailman import Mail
from flask_security import SQLAlchemyUserDatastore, Security, hash_password
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import configure_app_logging, PROJECT_ROOT
from app.helpers import register_globals
from app.limiter import limiter, add_limits_to_views

# Initial admin user.  Only create if db contains no admins
INITIAL_USER_PASSWORD = "example1"  # nosec B105, noqa: dodgy:password
INITIAL_USER_EMAIL    = "admin@example.com"

db = SQLAlchemy()
user_datastore = None  # pylint: disable=invalid-name
admin = None  # pylint: disable=invalid-name
cache = None  # pylint: disable=invalid-name
talisman = None  # pylint: disable=invalid-name


# pylint: disable=too-many-locals,too-many-statements
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

    # Set up Talisman
    csp = {
        'default-src': "'self'",
        'script-src': "'self' https://beacon.helpscout.net https://cdnjs.cloudflare.com " +
                      "https://cdn.jsdelivr.net https://beacon-v2.helpscout.net",
        'style-src': "'self' 'unsafe-inline' " +
                     "https://cdnjs.cloudflare.com https://cdn.jsdelivr.net " +
                     "https://fonts.googleapis.com",
        'style-src-elem': "'self' 'unsafe-inline' https://cdnjs.cloudflare.com " +
                     "https://cdn.jsdelivr.net https://fonts.googleapis.com",
        'style-src-attr': "'self'",
        'font-src': "'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com",
        'img-src': "'self' data: https://beacon.helpscout.net https://m.media-amazon.com " +
                   "*",  # allow images from anywhere, support book cover images
        'connect-src': "'self' https://beacon-v2.helpscout.net " +
                       "https://d3hb14vkzrxvla.cloudfront.net " +
                       "https://beaconapi.helpscout.net",
    }
    global talisman  # pylint: disable=global-statement
    talisman = Talisman(
        app,
        force_https=True,  # be sure to add --cert=adhoc to start up options for dev/test

        frame_options='DENY',
        frame_options_allow_from='None',

        strict_transport_security=False,  # defer https://github.com/dandoug/readinglist/issues/61
        strict_transport_security_include_subdomains=False,

        content_security_policy=csp,
        content_security_policy_report_only=False,  # switch to True to get reports but not blocked
        content_security_policy_report_uri='/csp-report',
        content_security_policy_nonce_in=['script-src', 'style-src'],

        referrer_policy='origin-when-cross-origin',  # used to return to add the book launch page

        session_cookie_secure=True,
        session_cookie_http_only=True,

        force_file_save=True,

        feature_policy={
            'geolocation': '\'none\''
        }
    )

    # handle being behind a reverse proxy, like in AWS Elastic Beanstalk
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_proto=1,  # Number of values to trust for X-Forwarded-Proto
        x_for=1,  # Number of values to trust for X-Forwarded-For
        x_host=1  # Number of values to trust for X-Forwarded-Host
    )

    # Bind limiter to app
    limiter.init_app(app)

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

    # Set route-specific limits we don't control directly not that they have all been defined
    add_limits_to_views(app)
    # Add limits specifically to the Flask-Login `/login` route
    limiter.limit("10 per minute", key_func=get_remote_address)(app.view_functions["security.login"])
    # Apply rate limiting to all routes in Flask-Admin and other security roles
    limiter.limit("30 per minute", key_func=get_remote_address)(app.blueprints["admin"])
    limiter.limit("30 per minute", key_func=get_remote_address)(app.blueprints["security"])

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
