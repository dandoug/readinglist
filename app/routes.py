from flask import current_app as app, render_template, request, jsonify, flash, redirect, url_for, g
from flask_security import roles_required, current_user, auth_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.services import fetch_product_details
from app.services import search_by_categories, get_book_by_id, search_by_author, \
    search_by_title, add_new_book, book_to_dict_with_status_and_feedback, \
    set_book_status, set_book_feedback, update_book, del_book, get_category_bs_tree, id_to_fullpath
from app.helpers import PLACEHOLDER, build_library_search_urls, compute_next_url
from app.forms import BookForm


@app.before_request
def add_global_vars():
    # Access the global Jinja environment, including in macros
    app.jinja_env.globals.update(current_user=current_user)


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

    status_filter = request.args.get('status', None)
    feedback_filter = request.args.get('feedback', None)

    if author:
        bks = search_by_author(author, status_filter, feedback_filter)
    elif title:
        bks = search_by_title(title, status_filter, feedback_filter)
    elif categories:
        # Decode encoded categories to full path strings before searching
        bks = search_by_categories([id_to_fullpath(category) for category in categories], status_filter, feedback_filter)
    else:
        # one of author, title or cat must be specified
        return jsonify({"error": "Missing author, title, or cat search parameter"}), 400, None

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
    # Extract 'author' and 'title' query parameters
    author = request.args.get('author')
    title = request.args.get('title')

    # Validate that both parameters are provided
    if not author or not title:
        return jsonify({"error": "Both 'author' and 'title' query parameters are required."}), 400

    return jsonify(build_library_search_urls(author, title))


@app.route('/add_book', methods=["GET", "POST"])
@roles_required('editor')
def add_book():
    form = BookForm(data=(request.form if request.method == "POST" else request.args))

    # If next not set, use the referrer if we have one, for where to go when done
    if not form.next.data:
        form.next.data = compute_next_url(request)

    if form.validate_on_submit():  # Checks if form is submitted and valid
        try:
            book = add_new_book(form)  # Attempt to add the book
            flash(f"Book id:{book.id} title:'{book.title}' added successfully!", "success")
            return redirect(form.next.data if form.next.data else url_for("index"))
        except ValueError as ve:  # Handle value-related issues (e.g., duplicate unique fields)
            flash(f"Failed to add book due to data error: {ve}", "danger")
        except RuntimeError as re:  # Handle unexpected runtime errors
            flash(f"An unexpected error occurred: {re}", "danger")
        except Exception as e:  # General fallback for any unanticipated exceptions
            flash(f"An error occurred while adding the book: {e}", "danger")
    return render_template("add_book.html", book_form=form)


@app.route('/edit_book', methods=["GET", "POST"])
@roles_required('editor')
def edit_book():
    form = BookForm(data=(request.form if request.method == "POST" else request.args))

    # If next not set, use the referrer if we have one, for where to go when done
    if not form.next.data:
        form.next.data = compute_next_url(request)

    if not form.id.data or not str(form.id.data).isdigit():  # Validate 'book_id'
        return jsonify({"error": "Invalid or missing 'id' parameter"}), 400

    if request.method == "POST":  # Check if the request method is POST
        if form.validate_on_submit():  # Checks if form is submitted and valid
            try:
                book = update_book(form)  # Attempt to update the book
                flash(f"Book id:{book.id} title:'{book.title}' updated successfully!", "success")
                # on successful update, go to next
                return redirect(form.next.data if form.next.data else url_for("index"))
            except ValueError as ve:  # Handle value-related issues (e.g., duplicate unique fields)
                flash(f"Failed to update book due to data error: {ve}", "danger")
            except RuntimeError as re:  # Handle unexpected runtime errors
                flash(f"An unexpected error occurred: {re}", "danger")
            except Exception as e:  # General fallback for any unanticipated exceptions
                flash(f"An error occurred while updating the book: {e}", "danger")
    else:
        # fill in book from database
        try:
            book = get_book_by_id(form.id.data)
            if not book:
                flash(f"Book with ID {form.id.data} not found.", "warning")
                return redirect(form.next.data if form.next.data else url_for("index"))
        except Exception as e:
            flash(f"Failed to get the book with ID {form.id.data}: {e}", "danger")
            return redirect(form.next.data if form.next.data else url_for("index"))

        if book:
            form.title.data = book.title
            form.author.data = book.author
            form.book_description.data = book.book_description
            form.asin.data = book.asin
            form.bestsellers_rank_flat.data = book.bestsellers_rank_flat
            form.categories_flat.data = book.categories_flat
            form.hardcover.data = book.hardcover
            form.image.data = book.image
            form.isbn_10.data = book.isbn_10
            form.isbn_13.data = book.isbn_13
            form.link.data = book.link
            form.rating.data = book.rating
    # return to or show initial edit form
    return render_template("edit_book.html", book_form=form)


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


@app.route('/delete_book', methods=["POST"])
@roles_required('admin')
def delete_book():
    # Validate required parameters
    book_id = request.form.get('book_id')

    if not book_id or not book_id.isdigit():
        return jsonify({"error": "Invalid or missing 'book_id' parameter"}), 400

    try:
        del_book(book_id)

        flash(f"Book id:{book_id} deleted successfully!", "success")
        return jsonify({"message": f"Book id:{book_id} deleted successfully!"}), 200
    except IntegrityError as e:
        flash(f"IntegrityError: {str(e)}")
        return jsonify({"error": "Cannot delete the book as it is referenced elsewhere"}), 400
    except SQLAlchemyError as e:
        flash(f"SQLAlchemyError: {str(e)}")
        return jsonify({"error": "An error occurred while processing the request"}), 500
    except Exception as e:
        flash(f"Unhandled exception: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route('/change_status', methods=["POST"])
@auth_required()
def change_status():
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
        return jsonify({"error": f"Invalid 'status' value. Allowed values: {', '.join(allowed_statuses)}"}), 400

    user_id = current_user.id
    set_book_status(book_id, status, user_id)
    return jsonify({'new_status': status}), 200


@app.route('/change_feedback', methods=["POST"])
@auth_required()
def change_feedback():
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
        return jsonify({"error": f"Invalid 'feedback' value. Allowed values: {', '.join(allowed_feedback)}"}), 400

    user_id = current_user.id
    set_book_feedback(book_id, fb, user_id)
    return jsonify({'new_feedback': fb}), 200
