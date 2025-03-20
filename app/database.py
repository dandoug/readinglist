from app.books import Book


def init_db(app):
    """
    Initializes the database connection for the application.

    :param app: The Flask application instance to configure the database for.
    :type app: Flask
    :return: None
    """
    from app import db
    with app.app_context():
        db.init_app(app)

        Book.bind(db)
