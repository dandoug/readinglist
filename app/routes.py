import os


def register_routes(app):
    """
    Register application routes to the given Flask app instance.

    This function sets up the necessary routes for the Flask application,
    allowing the app to handle HTTP requests properly. It connects specific
    URL routes to their corresponding view functions.

    :param app: The Flask application instance to register routes to.
    :type app: Flask
    :return: None
    """
    @app.route('/')
    def hello_world():  # put application's code here
        rds_port = os.getenv('RDS_PORT')
        return f"Hello World!  {rds_port}"
