from flask_security import current_user
from sqlalchemy import asc
from sqlalchemy.orm import contains_eager, noload

from app import db
from app.models import Book, ReadingStatus, Feedback


def search_by_categories(categories, status_filter: str = None,
                         feedback_filter: str = None) -> list[Book]:
    """
    Searches for books based on specified categories and optional filters for status and feedback.

    This function retrieves a list of books that match one or more categories. The results
    are sorted alphabetically by book title. Additional optional filters can be applied
    to refine the search results by user status or feedback.

    :param categories: A list of book categories to filter the query. The function will
        search for books matching any of the provided categories.
    :type categories: list

    :param status_filter: An optional status filter to further refine the query. Default
        is None.
    :type status_filter: str, optional

    :param feedback_filter: An optional feedback filter to apply additional
        refinement to the query. Default is None.
    :type feedback_filter: str, optional

    :return: A list of books that match the given criteria. Returns an empty list if
        no matching books are found or if no categories are provided.
    :rtype: list
    """
    if not categories:
        return []  # Return an empty list if no categories are provided

    # Query to search and sort books based on the provided requirements
    query = ((db.session.query(Book)
              .filter(Book.categories_flat.in_(categories)))  # match in one of the categories
             .order_by(asc(Book.title)))  # sort by title

    query = _add_user_status_and_feedback_joins(query)

    query = _add_status_and_feedback_filters(query, status_filter, feedback_filter)

    # execute the query
    return query.all()


def search_by_author(author: str, status_filter: str, feedback_filter: str) -> list[Book]:
    """Search for books by author's name."""
    return _search_by_attribute("author", author, status_filter, feedback_filter)


def search_by_title(title, status_filter: str, feedback_filter: str) -> list[Book]:
    """Search for books by title."""
    return _search_by_attribute("title", title, status_filter, feedback_filter)


_VALID_SEARCH_BY_ATTRIBUTES = {"author", "title"}


def _search_by_attribute(attribute: str, value: str, status_filter: str = None,
                         feedback_filter: str = None) -> list[Book]:
    """
    Searches for books in the database based on a specific attribute and value,
    with optional filters for book status and user feedback.

    This function executes a query on the `Book` database model, applying a
    case-insensitive partial match for the specified attribute with its value,
    and optionally filters the results by status or feedback. The query can
    also return all books sorted by the attribute when the value is "*".

    :param attribute: The attribute of the book to be searched by, such as 'title'
        or 'author'. The attribute must belong to the predefined valid attributes.
    :param value: The value to search for within the specified attribute. Supports
        case-insensitive partial matches.
    :param status_filter: Optional filter to apply for book status (default is None).
    :param feedback_filter: Optional filter to apply for user feedback (default
        is None).
    :return: A list of `Book` objects matching the search criteria and the optional
        filters.
    :rtype: list[Book]
    :raises ValueError: If the specified attribute is not a valid search attribute.
    """
    if attribute not in _VALID_SEARCH_BY_ATTRIBUTES:
        raise ValueError(f"Invalid attribute '{attribute}'. Must be one of {_VALID_SEARCH_BY_ATTRIBUTES}.")

    if not value:
        return []

    query = _add_user_status_and_feedback_joins(db.session.query(Book))

    # Order by the selected attribute
    query = query.order_by(asc(getattr(Book, attribute)))

    # Handle the special case for "*" to return all books sorted by the attribute
    if value != "*":
        # Perform a case-insensitive partial match (using ilike)
        query = query.filter(getattr(Book, attribute).ilike(f"%{value}%"))

    query = _add_status_and_feedback_filters(query, status_filter, feedback_filter)

    # execute the query
    books = query.all()

    return books


def _add_status_and_feedback_filters(query, status_filter, feedback_filter):
    if status_filter:
        if status_filter != "none":
            # handles read and up_next
            query = query.filter(ReadingStatus.status == status_filter)
        else:
            # finds only books without a status set
            query = query.filter(ReadingStatus.status.is_(None))
    if feedback_filter:
        if feedback_filter != "none":
            # handles like and dislike
            query = query.filter(Feedback.feedback == feedback_filter)
        else:
            # finds only books without a feedback set
            query = query.filter(Feedback.feedback.is_(None))
    return query


def _add_user_status_and_feedback_joins(query):
    # Add user status and feedback if there is an authenticated user
    user_id = current_user.id if current_user.is_authenticated else None
    if user_id:
        # Join feedback and status if user logged in
        query = ((query
        .outerjoin(
            ReadingStatus,
            (ReadingStatus.book_id == Book.id) & (
                    (ReadingStatus.user_id == user_id) | (ReadingStatus.user_id.is_(None))), ))
        .outerjoin(
            Feedback,
            (Feedback.book_id == Book.id) & ((Feedback.user_id == user_id) | (Feedback.user_id.is_(None))), )
        .options(
            contains_eager(Book.reading_statuses),
            contains_eager(Book.feedbacks)))
    else:
        # If no user logged in, status and feedback should be empty for all books, no joining
        query = (query
        .options(
            # Don't try to populate status or feedbacks when there's no user
            noload(Book.reading_statuses),
            noload(Book.feedbacks)))
    return query
