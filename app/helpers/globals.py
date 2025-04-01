from flask import jsonify
from flask_login import current_user

from app.helpers import parse_url


def register_globals(app):
    """
       Register global error handlers and context processors
    """
    # Define the 403 error handler
    @app.errorhandler(403)
    def access_forbidden(e):
        return jsonify({'error': f'You do not have permission to access this resource {e}'}), 403

    # Register the global Jinja2 context processor
    @app.context_processor
    def utility_processor():
        return {"parse_url": parse_url}

    @app.before_request
    def add_global_vars():
        # Access the global Jinja environment, including in macros
        app.jinja_env.globals.update(current_user=current_user)
