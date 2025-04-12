"""
This module is used to register global error handlers, context processors, and variables 
for a Flask application. It ensures that custom error handling, utility functions, and 
global variables (like `current_user`) are available to all templates and views.
"""
from flask import jsonify
from flask_login import current_user


def register_globals(app):
    """
    Register global error handlers, context processors, and variables for a Flask app.

    This function sets up custom error handlers, Jinja2 context processors, and global 
    variables to be made available throughout the lifecycle of a Flask request.
    """

    # Define the 403 error handler
    @app.errorhandler(403)
    def access_forbidden(e):
        """
        Handles 403 Forbidden errors by returning a JSON response with an error message.
        
        :param e: The exception that triggered the error
        :return: A JSON response object and a 403 HTTP status code
        """
        return jsonify({'error': f'You do not have permission to access this resource {e}'}), 403

    # Register the global Jinja2 context processor
    @app.context_processor
    def utility_processor():
        """
        Provides utility functions to the Jinja2 template context.

        Returns a dictionary of helper functions that can be accessed directly within templates.
        """
        from app.helpers.utilities import parse_url  # pylint: disable=import-outside-toplevel
        return {"parse_url": parse_url}

    @app.before_request
    def add_global_vars():
        """
        Adds global variables to the Jinja2 template environment before processing a request.

        Makes information like the `current_user` available globally to all templates and macros.
        """
        # Access the global Jinja environment, including in macros
        app.jinja_env.globals.update(current_user=current_user)
