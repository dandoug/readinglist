from flask import current_app as app, render_template, request, jsonify, flash, redirect, url_for
from flask_security import roles_required

from app.asin_data import fetch_product_details
from app.categories import get_category_bs_tree, id_to_fullpath
from app.books import search_by_categories, get_book_by_id, build_library_search_urls, search_by_author, \
    search_by_title, add_new_book
from app.forms import BookForm


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


@app.route('/add_book', methods=["GET", "POST"])
@roles_required('editor')
def add_book():
    form = BookForm()
    if form.validate_on_submit():  # Checks if form is submitted and valid
        try:
            book = add_new_book(form)  # Attempt to add the book
            flash(f"Book id:{book.id} title:'{book.title}' added successfully!", "success")
            return redirect(url_for("index"))
        except ValueError as ve:  # Handle value-related issues (e.g., duplicate unique fields)
            flash(f"Failed to add book due to data error: {ve}", "danger")
        except RuntimeError as re:  # Handle unexpected runtime errors
            flash(f"An unexpected error occurred: {re}", "danger")
        except Exception as e:  # General fallback for any unanticipated exceptions
            flash(f"An error occurred while adding the book: {e}", "danger")
    return render_template("add_book.html", book_form=form)


@app.route('/fill_by_asin', methods=["GET"])
@roles_required('editor')
def fill_by_asin():
    asin = request.args.get('asin')
    if not asin:
        return jsonify({"error": "Missing asin parameter"}), 400, None

    book_data = fetch_product_details(asin)
    if not book_data:
        return jsonify({"error": f"ASIN {asin} not found"}), 404, None
    return jsonify(book_data)
