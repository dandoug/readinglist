from sqlalchemy import asc, Column, Integer, String, Text, DECIMAL, MetaData
from sqlalchemy.orm import declarative_base
from urllib.parse import quote_plus


Base = declarative_base(metadata=MetaData())


class Book(Base):
    __tablename__ = 'books'

    @staticmethod
    def bind(db):
        Book.__bases__[0].metadata.bind = db.engine

    id = Column(Integer, primary_key=True, autoincrement=True)
    author = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    asin = Column(String(20), index=True)
    link = Column(Text)
    image = Column(Text)
    categories_flat = Column(String(255), index=True)
    book_description = Column(Text)
    rating = Column(DECIMAL(3, 2), index=True)
    isbn_13 = Column(String(17), index=True)
    isbn_10 = Column(String(13), index=True)
    hardcover = Column(String(64))
    bestsellers_rank_flat = Column(Text)
    specifications_flat = Column(Text)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def __repr__(self):
        return f"<Book(id={self.id}, title={self.title}, author={self.author})>"


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
    from app import db
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


def get_book_by_id(book_id):
    """
    Query the database and retrieve a book by its primary key (`book_id`).

    Args:
        book_id (int): The primary key of the book.

    Returns:
        Book: The book matching the provided `book_id`, or None if no match is found.
    """
    from app import db
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
