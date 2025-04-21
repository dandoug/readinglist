"""
This module provides search functionality for books in the database.

It includes methods to search books by categories, authors, or titles, with optional
filters for user-specific status and feedback. The queries are tailored to return
sorted results, refined to meet various search criteria. If a user is authenticated,
search results will include personalized status and feedback data.
"""
from flask_security import current_user
from sqlalchemy import asc, and_, exists, select, literal
from sqlalchemy.orm import contains_eager, noload, make_transient

from app import db
from app.models import Book, ReadingStatus, Feedback, TagBook, Tag


def search_by_categories(categories, status_filter: str = None,
                         feedback_filter: str = None, tag_filter: list[str] = None) -> list[Book]:
    """
    Searches for books based on categories and optional filters for status and feedback.
    
    This retrieves a list of books matching one or more categories. Results are sorted
    alphabetically by title. Optional filters can refine search results by user status 
    or feedback.
    """
    if not categories:
        return []  # Return an empty list if no categories are provided

    # Query to search and sort books based on the provided requirements
    query = ((db.session.query(Book)
              .filter(Book.categories_flat.in_(categories)))  # match in one of the categories
             .order_by(asc(Book.title)))  # sort by title

    query = _add_user_status_and_feedback_joins(query)

    query = _add_status_and_feedback_filters(query, status_filter, feedback_filter)

    query = query.filter(Book.tags.any(Tag.name.in_(tag_filter))) if tag_filter else query

    # execute the query
    bks = query.all()
    for book in bks:
        make_transient(book)
    db.session.expire_all()
    return bks


def search_by_author(author: str, status_filter: str,
                     feedback_filter: str, tag_filter: list[str]) -> list[Book]:
    """Search for books by author's name."""
    return _search_by_attribute("author", author, status_filter, feedback_filter, tag_filter)


def search_by_title(title, status_filter: str, feedback_filter: str, tag_filter: list[str]) -> list[Book]:
    """Search for books by title."""
    return _search_by_attribute("title", title, status_filter, feedback_filter, tag_filter)


_VALID_SEARCH_BY_ATTRIBUTES = {"author", "title"}


def _search_by_attribute(attribute: str, value: str, status_filter: str = None,
                         feedback_filter: str = None, tag_filter: list[str] = None) -> list[Book]:
    """
    Searches for books in the database by a specified attribute and value. Filters 
    for status and feedback can also be applied.
    
    This function queries the `Book` model, using a case-insensitive partial 
    match for the attribute's value. Filters can refine results by book status 
    or user feedback. When the value is "*", all books are returned sorted 
    by the attribute.

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

    # Add the tag filter if provided
    query = query.filter(Book.tags.any(Tag.name.in_(tag_filter))) if tag_filter else query

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
    user_id = current_user.id if current_user.is_authenticated else None
    if user_id:
        # Define a constant for EXISTS check
        # pylint: disable=invalid-name
        # noinspection PyPep8Naming
        EXISTS_CHECK = literal(1).label('exists_check')

        # Define the subquery to check for user's tags
        user_tag_exists = (
            select(EXISTS_CHECK)
            .select_from(Tag)
            .where(
                and_(
                    Tag.id == TagBook.tag_id,
                    Tag.owner_id == user_id
                )
            )
            .correlate(TagBook)
            .alias('user_tag_check')
        )

        query = (
            query
            # Join with ReadingStatus
            .outerjoin(
                ReadingStatus,
                and_(
                    ReadingStatus.book_id == Book.id,
                    ReadingStatus.user_id == user_id
                )
            )
            # Join with Feedback
            .outerjoin(
                Feedback,
                and_(
                    Feedback.book_id == Book.id,
                    Feedback.user_id == user_id
                )
            )
            # Join with TagBook using the exists subquery
            .outerjoin(
                TagBook,
                and_(
                    TagBook.book_id == Book.id,
                    exists(user_tag_exists)
                )
            )
            # Join with Tag
            .outerjoin(
                Tag,
                and_(
                    Tag.id == TagBook.tag_id,
                    Tag.owner_id == user_id
                )
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
        # If no user logged in, load no relationships
        query = query.options(
            noload(Book.reading_statuses),
            noload(Book.feedbacks),
            noload(Book.tags)
        )

    return query
