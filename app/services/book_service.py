from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.orm import noload

from app import db
from ..forms import BookForm
from app.models import Book, Feedback, ReadingStatus, FeedbackEnum, ReadingStatusEnum


def get_book_by_id(book_id, load_status=False, load_feedback=False):
    """
    Fetches a book object based on the provided book ID. The function allows
    loading or excluding related data such as reading statuses and feedbacks
    using the `load_status` and `load_feedback` flags.

    :param book_id: The ID of the book to retrieve.
    :type book_id: int
    :param load_status: A flag indicating whether to load reading statuses
        related to the book. Default is False.
    :type load_status: bool
    :param load_feedback: A flag indicating whether to load feedbacks
        related to the book. Default is False.
    :type load_feedback: bool
    :return: The book object corresponding to the provided ID, or None if
        not found.
    :rtype: Book or None
    """
    query = db.session.query(Book)
    if not load_status:
        query = query.options(noload(Book.reading_statuses))
    if not load_feedback:
        query = query.options(noload(Book.feedbacks))

    return query.filter_by(id=book_id).first()


def add_new_book(book_form: BookForm) -> Book:
    """
    Adds a new book to the database based on the provided book form. This function
    processes the data from the book form, creates a new Book object, and saves
    it to the database. If any duplicate or invalid data causes issues, it will
    handle the exceptions accordingly.

    :param book_form: The form containing information about the book to be added.

    :type book_form: BookForm

    :return: The newly added Book object.

    :rtype: Book

    :raises ValueError: If a book with the same unique constraint already exists.
    :raises RuntimeError: If a database request error or any unexpected error occurs.
    """
    try:
        # Create and add the new book
        new_book = Book(
            author=book_form.author.data,
            title=book_form.title.data,
            asin=book_form.asin.data,
            link=book_form.link.data,
            image=book_form.image.data,
            categories_flat=book_form.categories_flat.data,
            book_description=book_form.book_description.data,
            rating=book_form.rating.data or 0.0,
            isbn_13=book_form.isbn_13.data,
            isbn_10=book_form.isbn_10.data,
            hardcover=book_form.hardcover.data,
            bestsellers_rank_flat=book_form.bestsellers_rank_flat.data,
            specifications_flat=book_form.specifications_flat.data,
        )
        db.session.add(new_book)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("A book with the same unique constraint already exists.")
    except InvalidRequestError as e:
        db.session.rollback()
        raise RuntimeError(f"Database request error: {e}")
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"An unexpected error occurred: {e}")
    return new_book


def update_book(book_form: BookForm) -> Book:
    """
    Updates the details of an existing book in the database. It retrieves the book
    based on the provided ID in the book form, updates the book's attributes with new
    data, and commits the changes to the database. In the case of any errors during
    the database operation, the session is rolled back and appropriate exceptions
    are raised.

    :param book_form: Form containing updated data for a book
    :type book_form: BookForm
    :return: The updated book object
    :rtype: Book
    :raises ValueError: Raised when a unique constraint in the database is violated
    :raises RuntimeError: Raised in case of a database request error or any unexpected error
    """
    try:
        book = get_book_by_id(book_form.id.data)
        # Update the new book
        book.author = book_form.author.data
        book.title = book_form.title.data
        book.asin = book_form.asin.data
        book.link = book_form.link.data
        book.image = book_form.image.data
        book.categories_flat = book_form.categories_flat.data
        book.book_description = book_form.book_description.data
        book.rating = book_form.rating.data or 0.0
        book.isbn_13 = book_form.isbn_13.data
        book.isbn_10 = book_form.isbn_10.data
        book.hardcover = book_form.hardcover.data
        book.bestsellers_rank_flat = book_form.bestsellers_rank_flat.data
        book.specifications_flat = book_form.specifications_flat.data

        # Update the book in the database
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ValueError("A book with the same unique constraint already exists.")
    except InvalidRequestError as e:
        db.session.rollback()
        raise RuntimeError(f"Database request error: {e}")
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"An unexpected error occurred: {e}")
    return book


def del_book(book_id):
    """
    Deletes a book from the database based on the provided book ID.

    :param book_id: The ID of the book to delete.
    :type book_id: int
    :raises ValueError: If no book with the specified ID is found.
    """
    try:
        book = get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Book with ID {book_id} not found.")

        db.session.delete(book)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"An error occurred while deleting the book: {e}")


def get_book_status(book_id, user_id) -> ReadingStatusEnum:
    """
    Retrieve the reading status of a book for a specific user.

    This function queries the database for the reading status of a book
    associated with a specific user. If a status is found, it is returned;
    otherwise, the function will return None.

    :param book_id: The unique identifier of the book for which the reading
        status is being queried.
    :type book_id: int
    :param user_id: The unique identifier of the user for whom the reading
        status is being queried.
    :type user_id: int
    :return: The reading status of the book for the user, represented as
        a value in the ReadingStatusEnum enumeration, or None if no status
        is found.
    :rtype: ReadingStatusEnum | None
    """
    query = (db.session.query(ReadingStatus.status)
             .filter(ReadingStatus.book_id == book_id, ReadingStatus.user_id == user_id))
    row = query.one_or_none()
    return row.status if row else None


def get_book_feedback(book_id, user_id) -> FeedbackEnum:
    """
    Retrieves feedback for a specified book from a specific user. This function queries the
    database for a feedback record that matches the provided book ID and user ID. If a
    matching record exists, the function returns the feedback associated with it. If no
    record is found, it returns None.

    :param book_id: ID of the book for which feedback is being retrieved
    :param user_id: ID of the user providing the feedback
    :return: FeedbackEnum representing the feedback if found, otherwise None
    """
    query = (db.session.query(Feedback.feedback)
             .filter(Feedback.book_id == book_id, Feedback.user_id == user_id))
    row = query.one_or_none()
    return row.feedback if row else None


def set_book_status(book_id: int, status: str, user_id: int) -> dict:
    """
    Set the reading status of a book for a specific user. This function allows the user
    to update their reading status of a particular book, delete an existing status, or
    add a new status if it doesn't already exist. If the status is set to "none", any
    existing status for that book and user combination will be removed.

    :param book_id: The identifier of the book whose reading status is being modified.
    :type book_id: int
    :param status: The new reading status for the book. Accepted values are the status
        strings such as "none", "reading", "completed", etc.
    :type status: str
    :param user_id: The identifier of the user whose book reading status is being updated.
    :type user_id: int
    :return: A dictionary containing the updated details of the book, including its
        status and feedback for the given user.
    :rtype: dict
    """
    # Check if the reading status already exists for this user_id and book_id
    existing_status = db.session.query(
        ReadingStatus.id,
        ReadingStatus.status).filter_by(
        user_id=user_id,
        book_id=book_id
    ).first()

    # If "none", delete the reading status
    if status == "none":
        if existing_status:
            db.session.execute(
                delete(ReadingStatus)
                .where(ReadingStatus.id == existing_status.id)
            )
    else:
        if existing_status:
            # Update the current reading status
            db.session.execute(
                update(ReadingStatus)
                .where(ReadingStatus.id == existing_status.id)
                .values(status=status)
            )
        else:
            # Add a new reading status
            new_status = ReadingStatus(user_id=user_id, book_id=book_id, status=status)
            db.session.add(new_status)

    # Commit the transaction
    db.session.commit()


def set_book_feedback(book_id: int, fb: str, user_id: int) -> dict:
    """
    Updates or removes feedback for a specific book and user. If a feedback entry exists for the given
    user and book, it will be updated based on the provided feedback value. If the feedback is marked
    as "none", the existing feedback will be removed. If no feedback exists, a new entry will be created.
    Finally, the updated book details are fetched and returned.

    :param book_id: Identifier of the book for which the feedback is being set
    :type book_id: int
    :param fb: Feedback string provided by the user, set to "none" to delete feedback
    :type fb: str
    :param user_id: Identifier of the user providing the feedback
    :type user_id: int
    :return: A dictionary containing updated details of the book along with status and feedback data
    :rtype: dict
    """
    # Check if feedback already exists for this user_id and book_id
    existing_feedback = db.session.query(
        Feedback.id,
        Feedback.feedback).filter_by(
        user_id=user_id,
        book_id=book_id
    ).first()

    # If "none", delete the feedback
    if fb == "none":
        if existing_feedback:
            db.session.execute(
                delete(Feedback)
                .where(Feedback.id == existing_feedback.id)
            )
    else:
        if existing_feedback:
            # Update existing feedback
            db.session.execute(
                update(Feedback)
                .where(Feedback.id == existing_feedback.id)
                .values(feedback=fb)
            )
        else:
            # Insert new feedback if it wasn't there
            new_feedback = Feedback(user_id=user_id, book_id=book_id, feedback=fb)
            db.session.add(new_feedback)

    # Commit the transaction
    db.session.commit()


def book_to_dict_with_status_and_feedback(book, user_id):
    book_dict = book.to_dict()
    if user_id:
        fb = get_book_feedback(book_dict['id'], user_id)
        if fb:
            book_dict['feedback'] = fb.value
        status = get_book_status(book_dict['id'], user_id)
        if status:
            book_dict['status'] = status.value
    return book_dict
