"""
This module provides search functionality for books in the database.

It includes methods to search books by categories, authors, or titles, with optional
filters for user-specific status and feedback. The queries are tailored to return
sorted results, refined to meet various search criteria. If a user is authenticated,
search results will include personalized status and feedback data.
"""
from flask_security import current_user
from sqlalchemy import asc
from sqlalchemy.orm import contains_eager, noload, make_transient, load_only

from app import db
from app.models import Book, ReadingStatus, Feedback, TagBook, Tag


def search_by_categories(categories, status_filter: str = None,
                         feedback_filter: str = None) -> list[Book]:
    """
    Searches for books based on categories and optional filters for status and feedback.
    
    This retrieves a list of books matching one or more categories. Results are sorted
    alphabetically by title. Optional filters can refine search results by user status 
    or feedback.
    
    :param categories: A list of book categories to filter the query. Books matching 
        any of the categories will be retrieved.
    :type categories: list
    
    :param status_filter: An optional filter for book status. Default is None.
    :type status_filter: str, optional
    
    :param feedback_filter: An optional filter for feedback. Default is None.
    :type feedback_filter: str, optional
    
    :return: A list of books matching the criteria. Returns an empty list if no books 
        match or if categories are empty.
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
    bks = query.all()
    for book in bks:
        make_transient(book)
    db.session.expire_all()
    return bks


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
    Searches for books in the database by a specified attribute and value. Filters 
    for status and feedback can also be applied.
    
    This function queries the `Book` model, using a case-insensitive partial 
    match for the attribute's value. Filters can refine results by book status 
    or user feedback. When the value is "*", all books are returned sorted 
    by the attribute.
    
    :param attribute: The attribute to filter by, like 'title' or 'author'.
        Must be a valid attribute.
    :param value: The value for the attribute to be matched. Supports partial 
        case-insensitive matches.
    :param status_filter: An optional filter for status. Default is None.
    :type status_filter: str, optional
    :param feedback_filter: An optional filter for feedback. Default is None.
    :type feedback_filter: str, optional
    
    :return: A list of `Book` instances that meet the filters. An empty list is 
        returned if no matches are found.
    :rtype: list[Book]
    :raises ValueError: If the attribute provided is not valid.
    """
    if attribute not in _VALID_SEARCH_BY_ATTRIBUTES:
        raise ValueError(
            f"Invalid attribute '{attribute}'. Must be one of {_VALID_SEARCH_BY_ATTRIBUTES}."
        )
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
    for book in books:
        make_transient(book)
    db.session.expire_all()  # expire all books to prevent stale data from being returned

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
        query = (
            query
            .outerjoin(
                ReadingStatus,
                (ReadingStatus.book_id == Book.id)
                & (
                        (ReadingStatus.user_id == user_id)
                        | (ReadingStatus.user_id.is_(None))
                ),
            )
            .outerjoin(
                Feedback,
                (Feedback.book_id == Book.id)
                & (
                        (Feedback.user_id == user_id)
                        | (Feedback.user_id.is_(None))
                ),
            )
            .outerjoin(
                TagBook,
                (TagBook.book_id == Book.id)
            )
            .outerjoin(
                Tag,
                (Tag.id == TagBook.tag_id)
                & (Tag.owner_id == user_id)
            )
            .options(
                contains_eager(Book.reading_statuses).load_only(
                    ReadingStatus.id,
                    ReadingStatus.status
                ).noload(ReadingStatus.user),
                contains_eager(Book.feedbacks).load_only(
                    Feedback.id,
                    Feedback.feedback
                ).noload(Feedback.user),
                contains_eager(Book.tags).contains_eager(TagBook.tag),
                contains_eager(Book.tags).load_only(
                    TagBook.id,
                    TagBook.tag_id
                ),
                contains_eager(Book.tags).contains_eager(TagBook.tag).load_only(
                    Tag.id,
                    Tag.name,
                    Tag.color
                ),
                contains_eager(Book.tags).noload(TagBook.book),
                contains_eager(Book.tags).contains_eager(TagBook.tag).noload(Tag.owner)
            )
        )
    else:
        # If no user logged in, status, feedback, and tags should be empty for all books
        query = query.options(
            noload(Book.reading_statuses),
            noload(Book.feedbacks),
            noload(Book.tags)
        )

    return query
