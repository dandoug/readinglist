from flask import render_template
from sqlalchemy import text


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
        categories = get_category_list()
        return render_template('index.html', categories=categories)

    def get_category_list():
        from app import db
        with db.engine.connect() as conn:
            result = conn.execute(
                text("SELECT distinct categories_flat FROM readinglist.books order by categories_flat;"))
        categories = []
        for row in result:
            categories.append(row.categories_flat)
        return categories
