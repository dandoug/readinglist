"""
 Database service routines associated with tags.
"""
import re

import bleach

from app import db
from app.helpers.tag_colors import choose_random_color
from app.models import Tag, TagBook


def get_tags_for_user(user_id, q='') -> list[Tag]:
    """
    Retrieve a list of tags associated with a specific user. Optionally, filter the
    tags by a search query string.

    :param user_id: The unique identifier of the user whose tags are to be retrieved.
    :type user_id: int
    :param q: An optional search query string to filter the tags by their names.
    :type q: str
    :return: A list of Tag objects associated with the specified user and optionally
        filtered by the search query.
    :rtype: list[Tag]
    """
    query = db.session.query(Tag).filter(Tag.owner_id == user_id)
    if q:
        query = query.filter(Tag.name.ilike(f'%{q}%'))
    query = query.order_by(db.func.lower(Tag.name))
    return query.all()


def get_or_create_tag(user_id, tag_name) -> Tag:
    """
    Find an existing tag for this user or add a new one if it doesn't exist.
    :param user_id:
    :param tag_name:
    :return:
    """
    # First, sanitize the tag name to remove any HTML
    tag_name = bleach.clean(tag_name, tags=[], strip=True)

    # Then apply other validations
    if not tag_name or len(tag_name) > 32:
        raise ValueError("Tag name must be between 1 and 32 characters")

    # Validate tag name - allow only alphanumeric characters, hyphens, and spaces
    if not tag_name or not re.match(r'^[a-zA-Z0-9\s\-]+$', tag_name):
        raise ValueError("Tag names can only contain letters, numbers, spaces, and hyphens")

    tag_name = tag_name.lower()
    tag = db.session.query(Tag).filter(Tag.owner_id == user_id, Tag.name == tag_name).first()
    if tag:
        return tag

    tag = Tag(name=tag_name, owner_id=user_id, color=choose_random_color())
    db.session.add(tag)
    db.session.commit()
    return tag


def tag_book(tag_id, book_id, user_id) -> list[dict]:
    """
    Tags a book with a specific tag and returns the updated list of tags for the book.

    This function associates a given tag with a book by adding an entry to the TagBook
    table and committing it to the database. After successfully tagging the book, it
    retrieves and returns the updated list of tags associated with the book, including
    their names and colors, sorted by their IDs.

    :param tag_id: The ID of the tag to be associated with the book.
    :type tag_id: int
    :param book_id: The ID of the book that will be tagged.
    :type book_id: int
    :param user_id: The ID of the user performing the tagging operation. Only tags
        owned by this user will be included in the result.
    :type user_id: int
    :return: A list of dictionaries where each dictionary represents a tag associated
        with the book. Each dictionary contains the tag name and its corresponding color.
    :rtype: list[dict]
    """
    # Does the book already have this tag?
    book_tag = (db.session.query(TagBook)
                .filter(TagBook.tag_id == tag_id, TagBook.book_id == book_id)
                .first())
    if not book_tag:
        book_tag = TagBook(tag_id=tag_id, book_id=book_id)
        db.session.add(book_tag)
        db.session.commit()

    # return a new set of tags for the book, sorted in TagBook.id order
    return get_tags_and_colors(book_id, user_id)


def get_tags_for_user_with_colors(user_id) -> list[dict]:
    """
    Retrieve a list of tags and colors defined by a specific user.
    """
    tags = (db.session.query(Tag)
                 .filter(Tag.owner_id == user_id)
                 .order_by(Tag.id)
                 .all())
    # return a list of tags
    tag_and_colors = [{'value': tag.name, 'color': tag.color} for tag in tags]
    return tag_and_colors


def get_tags_and_colors(book_id, user_id):
    """
    Retrieve a list of tags and colors associated with a specific book for a specific user.

    This function queries the database for tags linked to a book, filters the tags
    to ensure they belong to a specific user, and then assembles a list of tags with
    their associated color details. The result includes all tags ordered by their
    tag-book association records.

    :param book_id: The unique identifier of the book to retrieve tags for.
    :type book_id: int
    :param user_id: The unique identifier of the user whose tags are to be retrieved.
    :type user_id: int
    :return: A list of dictionaries, where each dictionary contains the tag name and its color
        in the format {'tag': tag_name, 'color': tag_color}.
    :rtype: list[dict]
    """
    tag_books = (db.session.query(TagBook)
                 .options(db.joinedload(TagBook.tag))
                 .join(Tag, TagBook.tag_id == Tag.id)
                 .filter(
        TagBook.book_id == book_id,
        Tag.owner_id == user_id)
                 .order_by(TagBook.id)
                 .all())
    # return a list of tag and color objects for the book
    tag_and_colors = [{'value': tb.tag.name, 'color': tb.tag.color} for tb in tag_books]
    return tag_and_colors


def find_tag_for_user(tag_name, user_id) -> Tag or None:
    """
    Finds a tag for a specific user based on the tag's name and the user's ID.

    This function queries the database to find and return the tag that matches
    the given name and belongs to the specified user. If no matching tag is
    found, the function returns None.

    :param tag_name: The name of the tag to search for.
    :type tag_name: str
    :param user_id: The unique identifier of the user who owns the tag.
    :type user_id: int
    :return: The matching tag instance if found, or None if no match exists.
    :rtype: Tag or None
    """
    return db.session.query(Tag).filter(Tag.owner_id == user_id, Tag.name == tag_name).first()


def remove_tag_from_book(tag_id, book_id, user_id):
    """
    Removes a tag from a book and returns the updated list of tags associated with the book
    sorted by the TagBook.id. This function performs a deletion operation for the given
    tag-book association and commits the change to the database. Afterward, it retrieves
    and returns the updated set of tags for the book.

    :param tag_id: The unique identifier of the tag to be removed.
    :param book_id: The unique identifier of the book from which the tag will be removed.
    :param user_id: The unique identifier of the user associated with the operation.
    :return: The updated set of tags for the specified book, including their associated
        colors sorted by their TagBook.id.
    """
    db.session.query(TagBook).filter(TagBook.tag_id == tag_id, TagBook.book_id == book_id).delete()
    db.session.commit()

    # return a new set of tags for the book, sorted in TagBook.id order
    return get_tags_and_colors(book_id, user_id)
