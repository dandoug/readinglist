"""
This module defines the primary routes for the Flask application, providing endpoints
for rendering templates, searching, managing books, downloading data, and offering
application metadata. The routes include role-based access control, validation of 
user inputs, and interaction with both the database and external services as required.
"""
import csv
import io

from flask import (current_app as app, render_template, request, jsonify,
                   flash, redirect, url_for, make_response, Request, Response)
from flask_security import roles_required, current_user, auth_required

from app.models import Tag, Book
from app.services import (fetch_product_details, build_about_info, search_by_categories, get_book_by_id,
                          search_by_author, get_tags_for_user, get_or_create_tag,
                          tag_book, find_tag_for_user, get_tags_and_colors, remove_tag_from_book,
                          get_tags_for_user_with_colors, search_by_title, add_new_book,
                          book_to_dict_with_status_and_feedback, set_book_status, set_book_feedback,
                          update_book, del_book, get_category_bs_tree, id_to_fullpath)
from app.helpers import PLACEHOLDER, build_library_search_urls, compute_next_url
from app.forms import BookForm


@app.route('/')
def index():
    """
    Handles the root endpoint and renders the main page of the application. This
    function establishes the setup required for the app's main page by retrieving
    the binary search tree structure for the application's categories and
    passing it to the HTML template for rendering.

    :raises TemplateNotFound: If the specified template does not exist or cannot
        be loaded.

    :return: Response object containing the rendered HTML content for the main
        page, including the category binary search tree data.
    :rtype: werkzeug.wrappers.Response
    """
    category_bs_tree = get_category_bs_tree()
    return render_template('index.html', category_bs_tree=category_bs_tree)


@app.route('/about')
@roles_required('admin')
def about():
    """
    Handles the rendering of the 'About' page for administrators.

    This function is accessed via the '/about' route and is restricted to users
    with the 'admin' role. It gathers the necessary information for the 'About'
    page and passes it to the template for rendering.

    :parameters: None

    :raises: None

    :returns: Rendered HTML template of the 'About' page including the application
              information.
    """
    about_info = build_about_info()

    return render_template('about.html', about_info=about_info)


@app.route('/search', methods=['GET'])
def search():
    """
    Search for books.  Author, title, or cat must be specified.

    :return:
    """
    bks = _perform_search_base_on_args(request)

    if bks is None:
        # author, title, or cat must be specified
        return jsonify({"error": "bad search input"}), 400

    return render_template('results.html', books=bks, placeholder=PLACEHOLDER)


@app.route('/details', methods=['GET'])
def details():
    """
    The route '/details' allows fetching book
    information in JSON format by providing the book ID via the query
    parameter `id`.   For logged on users, the feedback and reading status
    of the book are also returned.
    """
    error, status, book = _check_for_required_book(request)
    if error:
        return error, status

    user_id = current_user.id if current_user.is_authenticated else None
    book_dict = book_to_dict_with_status_and_feedback(book, user_id)
    return jsonify(book_dict)


@app.route("/library_searches", methods=['GET'])
def library_searches():
    """
    Handles library search requests by constructing and returning URLs for
    searching library databases. The endpoint requires both 'author' and
    'title' query parameters to be provided in the request.

    :return: A JSON response with constructed library search URLs or an error
        message if required query parameters are missing.
    :rtype: flask.Response

    :raises ValueError: Raised with a 400 HTTP status if either 'author' or 'title' query
        parameters are missing from the request args.
    """
    # Extract 'author' and 'title' query parameters
    author = request.args.get('author')
    title = request.args.get('title')

    # Validate that both parameters are provided
    if not author or not title:
        return jsonify({"error": "Both 'author' and 'title' query parameters are required."}), 400

    return jsonify(build_library_search_urls(author, title))


@app.route('/download')
def download():
    """
    Handles the /download endpoint to perform a search operation and return results
    in CSV format based on provided query parameters. If no valid query parameters
    are provided or if the search yields no results, then responds with an error message.

    :raises HTTPException: Responds with status code 400 if input arguments are
        missing or result in no search results.

    :return: A Flask `Response` object containing the data in CSV format if the
         query parameters are valid and yield results, otherwise, a JSON error
         message with the appropriate error status code.
    """
    # Perform search based on input args
    bks = _perform_search_base_on_args(request)

    # input arguments did not result in search
    if bks is None:
        # author, title, or cat must be specified
        return jsonify({"error": "Bad search input parameter"}), 400

    response = _make_csv_response(bks)

    return response


@app.route('/add_book', methods=["GET", "POST"])
@roles_required('editor')
def add_book():
    """
    Handles the addition of a new book to the database. This function provides an interface
    for editors to add a book using a web form, processes the form, validates the submission,
    and performs the required operations to register the new book. Feedback is returned to the
    user depending on whether the operation succeeds or fails.

    The function operates in both GET and POST modes, rendering the submission form in GET
    operations and processing form data during POST operations.

    If the next field of the form is not set, the next URL is determined using the request's
    referrer. In case of a valid submission, it adds a new book to the database and redirects
    the user. If it fails, an appropriate error message is flashed.

    :raises Exception:
        If an unanticipated error occurs during the addition of the new book or database operation.
    :return:
        A rendered template containing the add-book form upon GET operation or the corresponding
        redirect statement upon successful form submission in POST operations.
    """
    form = BookForm(data=(request.form if request.method == "POST" else request.args))

    # If next not set, use the referrer if we have one, for where to go when done
    if not form.next.data:
        form.next.data = compute_next_url(request)

    if form.validate_on_submit():  # Checks if the form is submitted and valid
        try:
            book = add_new_book(form)  # Attempt to add the book
            flash(f"Book id:{book.id} title:'{book.title}' added successfully!", "success")
            return redirect(form.next.data if form.next.data else url_for("index"))
        except Exception as e:  # pylint: disable=broad-except
            flash(f"An error occurred while adding the book: {e}", "danger")
    return render_template("add_book.html", book_form=form)


@app.route('/edit_book', methods=["GET", "POST"])
@roles_required('editor')
def edit_book():
    """
    Handles the functionality for editing a book. This function is accessible only
    to users with the 'editor' role and supports both GET and POST HTTP methods.

    The function performs several crucial operations:
    1. Fetches and prepares the book editing form depending on the request method.
    2. Validates the 'id' form data to ensure it is provided and is in the correct
       format.
    3. If invoked via a POST request, it validates the form data, attempts to update
       the book, and handles potential exceptions.
    4. If invoked via a GET request, it retrieves the book from the database and
       populates the form using the book data.
    5. Displays appropriate messages or redirects users based on the success or
       failure of the operation.

    :param: None
    :raises: Ensures any system exceptions are caught and appropriately managed
             (e.g., database-related issues during book retrieval or update). The
             function does not re-raise exceptions but instead uses user-visible
             messages.
    :return: A rendered HTML page for editing a book in case of GET requests, or a
             redirection upon successful or failed form submission in POST requests.
    """
    form = BookForm(data=(request.form if request.method == "POST" else request.args))

    # If next not set, use the referrer if we have one, for where to go when done
    if not form.next.data:
        form.next.data = compute_next_url(request)

    if not form.id.data or not str(form.id.data).isdigit():  # Validate 'book_id'
        return jsonify({"error": "Invalid or missing 'id' parameter"}), 400

    if request.method == "POST":  # Check if the request method is POST
        if form.validate_on_submit():  # Checks if the form is submitted and valid
            try:
                book = update_book(form)  # Attempt to update the book
                flash(f"Book id:{book.id} title:'{book.title}' updated successfully!", "success")
                # on a successful update, go to next
                return redirect(form.next.data if form.next.data else url_for("index"))
            except Exception as e:  # pylint: disable=broad-except
                flash(f"An error occurred while updating the book: {e}", "danger")
    else:
        # fill in the book from the database
        try:
            book = get_book_by_id(form.id.data)
            if not book:
                flash(f"Book with ID {form.id.data} not found.", "warning")
                return redirect(form.next.data if form.next.data else url_for("index"))
        except Exception as e:  # pylint: disable=broad-except
            flash(f"Failed to get the book with ID {form.id.data}: {e}", "danger")
            return redirect(form.next.data if form.next.data else url_for("index"))

        if book:
            form.fill_from_book(book)
    # return to or show the initial edit form
    return render_template("edit_book.html", book_form=form)


@app.route('/fill_by_asin', methods=["GET"])
@roles_required('editor')
def fill_by_asin():
    """
    Handles a GET request to fetch and return product details by ASIN (Amazon Standard
    Identification Number). This function ensures that the authenticated user has the
    required 'editor' role to access this endpoint. It retrieves the 'asin' parameter
    from the request query string, validates its presence, and fetches the corresponding
    product details using the `fetch_product_details` function.

    If the 'asin' parameter is missing or cannot be found, appropriate error responses
    are returned to the client.

    :return: A JSON response containing either the product details fetched using the
        ASIN or an error message. If successful, the response contains the product
        details; otherwise, an error message indicating the issue (e.g., missing ASIN
        or not found) is returned.
    :rtype: flask.Response

    :raises flask.exceptions.BadRequest: If the 'asin' parameter is missing in the request.
    :raises flask.exceptions.NotFound: If the provided ASIN is not found in the database
        or external service.
    """
    asin = request.args.get('asin')
    if not asin:
        return jsonify({"error": "Missing asin parameter"}), 400, None

    book_data = fetch_product_details(asin)
    if not book_data:
        return jsonify({"error": f"ASIN {asin} not found"}), 404, None
    return jsonify(book_data)


@app.route('/delete_book', methods=["POST"])
@roles_required('admin')
def delete_book():
    """
    Deletes a book with a given identifier. This function ensures that necessary
    validation checks are performed on the provided book identifier and calls the
    appropriate deletion routine.

    The endpoint is protected and accessible only to users with the 'admin' role.
    It handles both success scenarios where the deletion is performed successfully
    and failure scenarios involving missing parameters or unexpected issues.

    :raises Exception: On encountering any unhandled issue during book deletion

    :return: A JSON response indicating the success of the operation, or an error
        message and HTTP status code in the event of a failure.
    """
    # Validate required parameters
    book_id = request.form.get('book_id')

    if not book_id or not book_id.isdigit():
        return jsonify({"error": "Invalid or missing 'book_id' parameter"}), 400

    try:
        del_book(book_id)

        flash(f"Book id:{book_id} deleted successfully!", "success")
        return jsonify({"message": f"Book id:{book_id} deleted successfully!"}), 200
    except Exception as e:  # pylint: disable=broad-except
        flash(f"Unhandled exception: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/change_status', methods=["POST"])
@auth_required()
def change_status():
    """
    Handles updating the status of a book for the authenticated user. This endpoint
    validates the input parameters for correctness, ensures that the status is among
    the allowed values, and updates the status of the specified book in the user's
    profile. It then returns the new status as a response. Only authenticated
    users are allowed to access this route.

    :raises ValueError: If the `book_id` parameter is missing or not a valid digit.
    :raises ValueError: If the `status` parameter is missing.
    :raises ValueError: If the `status` value is not within the allowed statuses.

    :return: A JSON object containing the updated book status.
    :rtype: Response
    """
    # Validate required parameters
    book_id = request.form.get('book_id')
    status = request.form.get('status')

    if not book_id or not book_id.isdigit():
        return jsonify({"error": "Invalid or missing 'book_id' parameter"}), 400

    if not status:
        return jsonify({"error": "Missing 'status' parameter"}), 400

    # Validate if status is supported
    allowed_statuses = ['read', 'up_next', 'none']
    if status not in allowed_statuses:
        allowed = ', '.join(allowed_statuses)
        return jsonify(
            {"error": f"Invalid 'status' value. Allowed values: {allowed}"}), 400

    user_id = current_user.id
    set_book_status(book_id, status, user_id)
    return jsonify({'new_status': status}), 200


@app.route('/change_feedback', methods=["POST"])
@auth_required()
def change_feedback():
    """
    Handles the change of feedback for a specific book. This function validates the
    input parameters, including `book_id` and `feedback`, ensures that the feedback
    value is within the allowed list of feedback states, and then updates the feedback
    for the given user and book in the system.

    :return: JSON object containing the updated feedback, or an error message in case
        of invalid input and the corresponding HTTP status code.
    :rtype: flask.Response
    """
    # Validate required parameters
    book_id = request.form.get('book_id')
    fb = request.form.get('feedback')

    if not book_id or not book_id.isdigit():
        return jsonify({"error": "Invalid or missing 'book_id' parameter"}), 400

    if not fb:
        return jsonify({"error": "Missing 'feedback' parameter"}), 400

    # Validate if feedback is supported
    allowed_feedback = ['like', 'dislike', 'none']
    if fb not in allowed_feedback:
        return jsonify({
            "error":
                f"Invalid 'feedback' value. Allowed values: {', '.join(allowed_feedback)}"}), 400

    user_id = current_user.id
    set_book_feedback(book_id, fb, user_id)
    return jsonify({'new_feedback': fb}), 200


@app.route('/autocomplete_tags')
@auth_required()
def autocomplete_tags():
    """
    Provides an endpoint to fetch tag suggestions based on a query for the
    authenticated user. The response contains matching tags and their associated
    colors.
    """
    q = request.args.get('q', '').lower()
    suggestions = get_tags_for_user(current_user.id, q)
    tags_and_colors = [{'name': s.name, 'color': s.color} for s in suggestions]
    return jsonify(tags_and_colors)


@app.route('/add_tag', methods=['POST'])
@auth_required()
def add_tag():
    """
    Handles the addition of a tag to a book for the current user. The function expects
    a JSON payload containing the tag name and the corresponding book ID. The user must
    be authenticated to access this endpoint. If the specified tag or book ID is invalid
    or missing, the function returns an error response. Otherwise, it ensures that the tag
    exists for the user, associates it with the given book, and returns the updated list
    of tags associated with the book.
    """
    tag, book, error, status = _check_for_required_tag_and_book(request, tag_create=True)
    if error:
        return error, status

    new_set_of_tags = tag_book(book_id=book.id, tag_id=tag.id, user_id=current_user.id)
    return jsonify({'success': True, 'tags': new_set_of_tags})


@app.route('/get_tags', methods=['GET'])
@auth_required()
def get_tags():
    """
    Handles the GET request to retrieve tags and their associated colors for a specific book.

    This function ensures the necessary book data is present and authenticated
    before returning the requested tags and colors. If no valid book is found,
    an error response is returned.
    """
    error, status, book = _check_for_required_book(request)
    if error:
        return error, status

    return jsonify({'success': True, 'tags': get_tags_and_colors(book_id=book.id, user_id=current_user.id)})


@app.route('/get_user_tags', methods=['GET'])
@auth_required()
def get_user_tags():
    """
    Handles the GET request to retrieve tags and their associated colors for a user.
    """
    return jsonify({'success': True, 'tags': get_tags_for_user_with_colors(user_id=current_user.id)})


@app.route('/remove_tag', methods=['POST'])
@auth_required()
def remove_tag():
    """
    Handles the removal of a tag associated with a book for an authenticated user.

    This function receives a JSON payload from an HTTP POST request, extracts
    the tag name and book ID, and performs the following operations:
    - Validates the presence and correctness of the input parameters.
    - Checks the existence of the book with the given ID in the system.
    - Verifies that the specified tag is associated with the authenticated user.
    - If the tag exists and is associated with the user, removes the tag from
      the book and returns the updated set of tags for the book.

    If a validation or existence check fails, an appropriate error response is
    returned.

    :return: A JSON response indicating the success or failure of the operation.
    :rtype: flask.Response
    :raises ValueError: If the `book_id` is not a valid integer.
    :raises KeyError: If `tag` or `book_id` is missing in the request payload.
    """
    tag, book, error, status = _check_for_required_tag_and_book(request)
    if error:
        return error, status

    user_id = current_user.id
    if not tag:
        # if the tag doesn't exist, then it can't be assigned to a book
        # just get the current set of tags and return them
        return (
            jsonify({'success': True,
                     'tags': get_tags_and_colors(book_id=book.id, user_id=user_id)}))
    # perform the removal and return the new set of tags
    new_set_of_tags = remove_tag_from_book(tag_id=tag.id, book_id=book.id, user_id=user_id)
    return jsonify({'success': True, 'tags': new_set_of_tags})


def _check_for_required_tag_and_book(req, tag_create=False) -> (Tag, Book, Response, int):
    tag_name = req.json.get('tag')
    book_id = req.json.get('book_id')

    if not tag_name or not book_id:
        return None, None, jsonify({"error": "Missing or invalid parameters"}), 400
    # check that book exists
    book = get_book_by_id(book_id)
    if not book:
        return None, None, jsonify({"error": f"Book {book_id} not found"}), 400
    # check if tag exists for user
    tag_name = tag_name.lower()
    if tag_create:
        tag = get_or_create_tag(user_id=current_user.id, tag_name=tag_name)
    else:
        tag = find_tag_for_user(user_id=current_user.id, tag_name=tag_name)

    return tag, book, None, 200


def _check_for_required_book(req):
    """
    Validates the presence and format of the 'id' parameter in the request and retrieves the
    associated book object. If the 'id' is missing or invalid, or if the book does not exist, 
    an appropriate error response is returned.

    :param req: The Flask request object containing query parameters.
                Expects the 'id' parameter in the request arguments.
    :type req: flask.Request
    :return: A tuple containing:
             - An error response (if applicable) or None,
             - The corresponding HTTP status code,
             - The retrieved book object or None.
    :rtype: tuple
    """
    book_id = req.args.get('id')
    if not book_id or not book_id.isdigit():
        return jsonify({"error": "Invalid or missing 'id' parameter"}), 400, None

    book = get_book_by_id(book_id,
                          current_user.id if current_user.is_authenticated else None,
                          load_status=True, load_feedback=True)
    if not book:
        return jsonify({"error": f"Book {book_id} not found"}), 404, None

    return None, 200, book


def _perform_search_base_on_args(req: Request):
    """
    Performs a search for books based on arguments provided in the request object. The search
    can be filtered by author, title, or categories, with additional options such as status and
    feedback filters. The result set can also be sorted based on the provided sort criteria.

    :param req: A Request object containing search arguments and options. The following arguments
        are handled:
        - author (str): Author's name to filter books by.
        - title (str): Book title to filter books by.
        - cat (list[str]): List of category IDs to filter books by (decoded into full path
            strings).
        - status (Optional[str]): Status filter for books (e.g., available, checked-out).
        - feedback (Optional[str]): Feedback filter for books (e.g., positive, negative).
        - sortColumn (Optional[str]): Column to sort books by; valid values are 'title',
            'author', or 'rating'.
        - sortOrder (Optional[str]): Order to sort books; valid values are 'asc' (ascending) or
            'desc' (descending).

    :return: 
        - A sorted list of books that match the search criteria if valid sorting and filtering
            options are provided.
        - None if no search criteria are provided or if invalid filter/sort options are supplied.
    """
    author = req.args.get('author')
    title = req.args.get('title')
    categories = req.args.getlist('cat')

    status_filter = req.args.get('status', None)
    feedback_filter = req.args.get('feedback', None)

    tag_filter = req.args.getlist('tag')
    # make sure all lower case
    tag_filter = [tag.lower() for tag in tag_filter]

    sort_column = req.args.get('sortColumn', None)
    sort_order = req.args.get('sortOrder', 'asc')

    if author:
        bks = search_by_author(author, status_filter, feedback_filter, tag_filter)
    elif title:
        bks = search_by_title(title, status_filter, feedback_filter, tag_filter)
    elif categories:
        # Decode encoded categories to full path strings before searching
        bks = search_by_categories(
            [id_to_fullpath(category) for category in categories], status_filter, feedback_filter, tag_filter)
    else:
        return None

    # if sort criteria were supplied, then apply them
    if sort_column:
        # Verify sort criteria.  Returning None to our caller will return 400 to the browser
        if sort_column not in ['title', 'author', 'rating']:
            return None  # invalid input
        if sort_order not in ['asc', 'desc']:
            return None  # invalid input
        # sort the books
        reverse_order = sort_order == 'desc'
        bks = sorted(bks, key=lambda bk: getattr(bk, sort_column, ''), reverse=reverse_order)

    return bks


def _make_csv_response(bks):
    """
    Generates a CSV response from a list of books.

    This function takes a list of book objects and creates a CSV file in-memory.
    The CSV file includes predefined columns for book attributes. It then creates
    an HTTP response containing the CSV content, suitable for file download. Missing
    data fields are replaced with default values such as 'none'.

    :param bks: A list of book objects to be written into the CSV.
    :type bks: list
    :return: Flask response containing the generated CSV data.
    :rtype: flask.Response
    """
    # Create an in-memory buffer
    output = io.StringIO()
    # Use csv.writer to write CSV data into the buffer
    writer = csv.writer(output)
    # Write header row
    writer.writerow([
        "Id",
        "Title",
        "Author",
        "Rating",
        "Description",
        "Feedback",
        "Pages",
        "Categories",
        "Booksellers_Rank",
        "ASIN",
        "ISBN-10",
        "ISBN-13",
        "Amazon_Link",
        "Cover_Image",
        "Status",
        "Tags",
        "Specifications"
    ])
    for bk in bks:
        tags = bk.tags;
        if tags:
            tag_str = ', '.join(map(lambda t: t.tag.name.lower().replace(' ','-'), tags))
        else:
            tag_str = ''
        writer.writerow([
            bk.id,
            _safe_string(bk.title),
            _safe_string(bk.author),
            bk.rating,
            _safe_string(bk.book_description),
            bk.feedbacks[0].feedback.value if bk.feedbacks else 'none',
            bk.hardcover,
            bk.categories_flat,
            bk.bestsellers_rank_flat,
            bk.asin,
            bk.isbn_10,
            bk.isbn_13,
            bk.link,
            bk.image,
            bk.reading_statuses[0].status.value if bk.reading_statuses else 'none',
            tag_str,
            bk.specifications_flat
        ])
    # Get the CSV content from the buffer
    csv_content = output.getvalue()
    output.close()
    # Create a response object
    response = make_response(csv_content)
    # Set headers for file download
    response.headers["Content-Disposition"] = "attachment; filename=booklist.csv"
    response.mimetype = "text/csv"
    return response


def _safe_string(in_str: str) -> str:
    """
    Replace all 0xA0 (non-breaking space) characters in the input string with 0x20 (regular space).

    :param in_str: The input string to process.
    :type in_str: str
    :return: A new string with all non-breaking spaces replaced by regular spaces.
    :rtype: str
    """
    if not in_str:
        return ''
    return in_str.replace('\xa0', ' ')
