from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import asc
from urllib.parse import quote_plus

from . import db


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
    results = (
        db.session.query(Book)
        .filter(Book.categories_flat.in_(categories))  # Match one of the categories
        .order_by(
            asc(Book.categories_flat),  # Sort by categories_flat
            asc(Book.author),  # Then by author
            asc(Book.title)  # Finally by title
        )
        .all()  # Fetch all matching records
    )

    return results


VALID_SEARCH_BY_ATTRIBUTES = {"author", "title"}


def _search_by_attribute(attribute: str, value: str):
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

    # Handle the special case for "*" to return all books sorted by the attribute
    if value == "*":
        return db.session.query(Book).order_by(asc(getattr(Book, attribute))).all()

    # Perform a case-insensitive partial match (using ilike)
    return (
        db.session.query(Book)
        .filter(getattr(Book, attribute).ilike(f"%{value}%"))
        .order_by(asc(getattr(Book, attribute)))
        .all()
    )


def search_by_author(author):
    """Search for books by author's name."""
    return _search_by_attribute("author", author)


def search_by_title(title):
    """Search for books by title."""
    return _search_by_attribute("title", title)


def get_book_by_id(book_id):
    """
    Query the database and retrieve a book by its primary key (`book_id`).

    Args:
        book_id (int): The primary key of the book.

    Returns:
        Book: The book matching the provided `book_id`, or None if no match is found.
    """
    return db.session.query(Book).filter_by(id=book_id).first()


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
