from markupsafe import Markup
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from flask_security import current_user
from sqlalchemy.orm import mapped_column, Mapped, relationship, contains_eager, declared_attr, noload
from sqlalchemy import asc, ForeignKey, Enum
from urllib.parse import quote_plus
from enum import Enum as PyEnum

from . import db
from .forms import BookForm


class ReadingStatusEnum(PyEnum):
    up_next = "up_next"
    read = "read"


class ReadingStatus(db.Model):
    __tablename__ = "reading_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    status: Mapped[ReadingStatusEnum] = mapped_column(Enum(ReadingStatusEnum))
    book: Mapped["Book"] = relationship(back_populates="reading_statuses", lazy="joined")

    @declared_attr
    def user(self) -> Mapped["User"]:
        return relationship("User", back_populates="reading_statuses", lazy="joined")


class FeedbackEnum(PyEnum):
    like = "like"
    dislike = "dislike"


class Feedback(db.Model):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    feedback: Mapped[FeedbackEnum] = mapped_column(Enum(FeedbackEnum))
    book: Mapped["Book"] = relationship(back_populates="feedbacks", lazy="joined")

    @declared_attr
    def user(self) -> Mapped["User"]:
        return relationship("User", back_populates="feedbacks", lazy="joined")


class Book(db.Model):
    """
    Represents a book entity in the database.

    This class is mapped to the `books` table in the database and is used to store
    and manage information about books such as title, author, description, and related attributes.
    The class provides methods to convert its instance to a dictionary and to return a string
    representation of the object.

    :ivar id: Unique identifier for the book.
    :type id: int
    :ivar author: Name of the author of the book.
    :type author: str
    :ivar title: Title of the book.
    :type title: str
    :ivar asin: Amazon Standard Identification Number (ASIN) of the book,
        if available.
    :type asin: Optional[str]
    :ivar link: URL linking to the book's details, if available.
    :type link: Optional[str]
    :ivar image: URL linking to the book's image, if available.
    :type image: Optional[str]
    :ivar categories_flat: Flattened string representation of the
        book's categories, if available.
    :type categories_flat: Optional[str]
    :ivar book_description: Description of the book, if available.
    :type book_description: Optional[str]
    :ivar rating: Rating of the book, defaults to 0.0.
    :type rating: float
    :ivar isbn_13: International Standard Book Number (13-digit),
        if available.
    :type isbn_13: Optional[str]
    :ivar isbn_10: International Standard Book Number (10-digit),
        if available.
    :type isbn_10: Optional[str]
    :ivar hardcover: Indicates hardcover details of the book, if available.
    :type hardcover: Optional[str]
    :ivar bestsellers_rank_flat: Flattened string representation of the book's
        bestsellers rank, if available.
    :type bestsellers_rank_flat: Optional[str]
    :ivar specifications_flat: Flattened string representation of the book's
        specifications, if available.
    :type specifications_flat: Optional[str]
    """
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    asin: Mapped[str | None] = mapped_column(db.String(20), index=True, nullable=True)
    link: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    image: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    categories_flat: Mapped[str | None] = mapped_column(db.String(255), index=True, nullable=True)
    book_description: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    rating: Mapped[float] = mapped_column(db.Float, default=0.0, index=True, nullable=False)
    isbn_13: Mapped[str | None] = mapped_column(db.String(17), index=True, nullable=True)
    isbn_10: Mapped[str | None] = mapped_column(db.String(13), index=True, nullable=True)
    hardcover: Mapped[str | None] = mapped_column(db.String(64), nullable=True)
    bestsellers_rank_flat: Mapped[str | None] = mapped_column(db.Text, nullable=True)
    specifications_flat: Mapped[str | None] = mapped_column(db.Text, nullable=True)

    reading_statuses: Mapped[list["ReadingStatus"]] = relationship(back_populates="book")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="book")

    def to_dict(self) -> dict:
        """Converts the model instance into a dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def __repr__(self) -> str:
        """Provides a clean string representation of the object."""
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"


def search_by_categories(categories):
    """
    Search for books where the `categories_flat` value matches any value in `categories`.

    Args:
        categories (list of str): List of category strings to match.

    Returns:
        list: List of books matching the input categories, sorted by `categories_flat`,
              `author`, and `title`.
    """
    if not categories:
        return []  # Return an empty list if no categories are provided

    # Query to search and sort books based on the provided requirements
    query = ((db.session.query(Book)
              .filter(Book.categories_flat.in_(categories)))  # match in one of the categories
             .order_by(asc(Book.title)))  # sort by title

    query = _add_user_status_and_feedback_joins(query)

    # execute the query
    return query.all()


def _add_user_status_and_feedback_joins(query):
    # Add user status and feedback if there is an authenticated user
    user_id = current_user.id if current_user.is_authenticated else None
    if user_id:
        # Join feedback and status if user logged in
        query = ((((query
            .outerjoin(ReadingStatus, ReadingStatus.book_id == Book.id))
            .outerjoin(Feedback, Feedback.book_id == Book.id))
            .filter(
                (ReadingStatus.user_id == user_id) | (ReadingStatus.user_id.is_(None)),
                (Feedback.user_id == user_id) | (Feedback.user_id.is_(None))))
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


VALID_SEARCH_BY_ATTRIBUTES = {"author", "title"}


def _search_by_attribute(attribute: str, value: str) -> list[Book]:
    """
    Common helper to search books by a specific attribute.

    Args:
        attribute (str): The name of the book attribute to search (e.g., 'author', 'title').
        value (str): The search value.

    Returns:
        list: List of `Book` objects matching the search criteria.

    Raises:
        ValueError: If the attribute is not valid.
    """
    if attribute not in VALID_SEARCH_BY_ATTRIBUTES:
        raise ValueError(f"Invalid attribute '{attribute}'. Must be one of {VALID_SEARCH_BY_ATTRIBUTES}.")

    if not value:
        return []

    query = _add_user_status_and_feedback_joins(db.session.query(Book))

    # Order by the selected attribute
    query = query.order_by(asc(getattr(Book, attribute)))

    # Handle the special case for "*" to return all books sorted by the attribute
    if value != "*":
        # Perform a case-insensitive partial match (using ilike)
        query = query.filter(getattr(Book, attribute).ilike(f"%{value}%"))

    # execute the query
    books = query.all()

    return books


def search_by_author(author):
    """Search for books by author's name."""
    return _search_by_attribute("author", author)


def search_by_title(title):
    """Search for books by title."""
    return _search_by_attribute("title", title)


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


SEARCH_TEMPLATES = {
    "Los Gatos Library": "https://losgatos.aspendiscovery.org/Search/Results?join=AND&bool0[]=AND&lookfor0[]={title}&type0[]=Title&lookfor0[]={author}&type0[]=Author&submit=Find",
    "Santa Clara Country Library": "https://sccl.bibliocommons.com/v2/search?custom_edit=false&query=(title%3A({title})%20AND%20contributor%3A({author}))&searchType=bl&suppress=true",
    "San Diego Library": "https://sandiego.bibliocommons.com/v2/search?custom_edit=false&query=(title%3A({title})%20AND%20contributor%3A({author})%20)&searchType=bl&suppress=true",
    "San Diego County Library": "https://sdcl.bibliocommons.com/v2/search?custom_edit=false&query=(anywhere%3A({title})%20AND%20anywhere%3A({author})%20)&searchType=bl&suppress=true",
    "Placer County Library": "https://placer.polarislibrary.com/polaris/search/searchresults.aspx?type=Advanced&term={title}&relation=ALL&by=TI&term2={author}&relation2=ALL&by2=AU&bool1=AND&limit=TOM=*&sort=RELEVANCE&page=0",
    "Nevada County Library": "https://library.nevadacountyca.gov/polaris/search/searchresults.aspx?ctx=1.1033.0.0.1&type=Advanced&term={title}&relation=ALL&by=TI&term2={author}&relation2=ALL&by2=AU&bool1=AND&bool4=AND&limit=(TOM=*%20AND%20OWN=1)&sort=RELEVANCE&page=0&searchid=1"
}


def build_library_search_urls(book):
    """
    Generates search URLs for a library system based on a given book's title and author.
    The function uses predefined templates to construct the URLs by encoding the book's
    title and author and replacing placeholders in the template strings.

    :param book: An object representing a book with properties `title` and `author`.
    :type book: Book
    :return: A dictionary of search URLs where keys are search provider identifiers
             and values are the constructed URLs with the book title and author
             information encoded.
    :rtype: dict
    """
    escaped_title = quote_plus(book.title, safe="")
    escaped_author = quote_plus(book.author, safe="")
    search_urls = {
        key: value.replace("{title}", escaped_title).replace("{author}", escaped_author)
        for key, value in SEARCH_TEMPLATES.items()
    }
    return search_urls


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


def render_icon(item, icon_mapping, span_id, default_icon="fa-check"):
    # item is the enumeration value (like 'like', 'read'),
    # icon_mapping is a dictionary mapping enum values to font-awesome icons
    if item in icon_mapping:
        return Markup(f'<span id="{span_id}"><i class="fa {icon_mapping[item]}" aria-hidden="true"></i></span>')
    # not in mapping, just use hidden default as a spacer
    return Markup(f'<span id="{span_id}"><i class="fa {default_icon}" aria-hidden="true" style="visibility: hidden;"></i></span>')


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
    query = (db.session.query(ReadingStatus)
             .filter(ReadingStatus.book_id == book_id, ReadingStatus.user_id == user_id))
    status = query.one_or_none()
    if status:
        return status.status
    else:
        return None


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
    query = (db.session.query(Feedback)
             .filter(Feedback.book_id == book_id, Feedback.user_id == user_id))
    fb = query.one_or_none()
    if fb:
        return fb.feedback
    else:
        return None


def set_book_status(book_id: int, status: str, user_id: int) -> dict:
    """
    Upserts a reading status for a user and book.

    :param book_id: The ID of the book whose status is being updated.
    :param status: The new status as a string. Must be convertible to ReadingStatusEnum or 'none'
    :param user_id: The ID of the user for whom the status is being updated.
    """
    if status == "none":
        stmt = db.delete(ReadingStatus).where(
            ReadingStatus.user_id == user_id,
            ReadingStatus.book_id == book_id
        )
    else:
        stmt = insert(ReadingStatus).values(
            user_id=user_id,
            book_id=book_id,
            status=status
        )
        # Add ON DUPLICATE KEY UPDATE clause
        stmt = stmt.on_duplicate_key_update({"status": status})

    # Use Flask-SQLAlchemy's db.session for execution
    db.session.execute(stmt)
    db.session.commit()

    book = get_book_by_id(book_id)
    return book_to_dict_with_status_and_feedback(book, user_id)


def set_book_feedback(book_id: int, fb: str, user_id: int) -> dict:
    """
    Sets feedback for a book by a user. This function allows adding, updating,
    or deleting feedback based on the given `fb` parameter. If the feedback
    (`fb`) is "none", the feedback for the specific book by the specified user
    is removed. Otherwise, new feedback is inserted or existing feedback is updated.

    :param book_id: The unique identifier of the book for which feedback is being
        set.
    :type book_id: int
    :param fb: The feedback string provided by the user. If set to "none",
        the feedback is removed.
    :type fb: str
    :param user_id: The unique identifier of the user providing the feedback.
    :type user_id: int
    :return: A dictionary containing the updated book data, feedback status,
        and the feedback details after processing.
    :rtype: dict
    """
    if fb == "none":
        stmt = db.delete(Feedback).where(
            Feedback.user_id == user_id,
            Feedback.book_id == book_id
        )
    else:
        stmt = insert(Feedback).values(
            user_id=user_id,
            book_id=book_id,
            feedback=fb
        )
        # Add ON DUPLICATE KEY UPDATE clause
        stmt = stmt.on_duplicate_key_update({"feedback": fb})

    # Use Flask-SQLAlchemy's db.session for execution
    db.session.execute(stmt)
    db.session.commit()

    book = get_book_by_id(book_id)
    return book_to_dict_with_status_and_feedback(book, user_id)

