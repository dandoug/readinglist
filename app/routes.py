from flask import render_template, request, jsonify

from app.categories import get_category_bs_tree, id_to_fullpath
from app.books import search_by_categories, get_book_by_id, build_library_search_urls


def _check_for_required_book(req):
    """
    Checks for the required book based on the 'id' parameter provided in the request and returns appropriate
    responses in cases of an invalid or missing ID, or if the book with the given ID does not exist.

    :param req: Flask request object containing request arguments.
    :type req: flask.request.Request
    :return:
        A tuple containing three values:
            - A JSON response object with an error message or None.
            - HTTP status code (400 or 404 in case of errors, None if successful).
            - The book object if it exists, otherwise None.
    :rtype: tuple
    """
    book_id = req.args.get('id')
    if not book_id or not book_id.isdigit():
        return jsonify({"error": "Invalid or missing 'id' parameter"}), 400, None

    book = get_book_by_id(book_id)
    if not book:
        return jsonify({"error": f"Book {book_id} not found"}), 404, None

    return None, 200, book


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
    def index():  # put application's code here
        category_bs_tree = get_category_bs_tree()
        return render_template('index.html', category_bs_tree=category_bs_tree)

    @app.route('/search', methods=['GET'])
    def search():
        """
        Registers application routes including the `/search` endpoint functionality.

        The `/search` route is designed to handle GET requests that include category
        parameters. These parameters are processed to obtain full path strings and
        are used to perform a book search. Depending on the presence of valid input
        categories, results are rendered in an HTML template or returned as JSON
        response.
        """
        # Extract category params and decode to full path strings
        categories_fullpath = [
            id_to_fullpath(category) for category in request.args.getlist('cat')
        ]

        if categories_fullpath:
            bks = search_by_categories(categories_fullpath)
            return render_template('results.html', books=bks)
        else:
            return jsonify({
                'categories_fullpath': categories_fullpath
            })

    @app.route('/details', methods=['GET'])
    def details():
        """
        Registers API routes for the application and defines a single endpoint
        to fetch book details by ID. The route '/details' allows fetching book
        information in JSON format by providing the book ID via the query
        parameter `id`.
        """
        error, status, book = _check_for_required_book(request)
        if error:
            return error, status
        return jsonify(book.to_dict())

    @app.route("/library_searches", methods=['GET'])
    def library_searches():
        error, status, book = _check_for_required_book(request)
        if error:
            return error, status

        return jsonify(build_library_search_urls(book))
