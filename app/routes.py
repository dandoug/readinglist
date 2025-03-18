from flask import render_template, request, jsonify

from app.categories import get_category_bs_tree, id_to_fullpath
from app.books import search_by_categories, get_book_by_id, build_library_search_urls, search_by_author, search_by_title


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
        Search for books.  One of author, title or cat must be specified.

        :return:
        """
        author = request.args.get('author')
        title = request.args.get('title')
        categories = request.args.getlist('cat')

        if author:
            bks = search_by_author(author)
        elif title:
            bks = search_by_title(title)
        elif categories:
            # Decode encoded categories to full path strings before searching
            bks = search_by_categories([id_to_fullpath(category) for category in categories])
        else:
            # one of author, title or cat must be specified
            return jsonify({"error": "Missing author, title, or cat search parameter"}), 400, None

        return render_template('results.html', books=bks)

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
        # some descriptions have &nbsp; and these need to be rendered as just space... no markup allowed here
        book.book_description = book.book_description.replace('\u00A0', '\u0020')

        return jsonify(book.to_dict())

    @app.route("/library_searches", methods=['GET'])
    def library_searches():
        error, status, book = _check_for_required_book(request)
        if error:
            return error, status
        return jsonify(build_library_search_urls(book))
