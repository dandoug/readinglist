from sqlalchemy import asc, Column, Integer, String, Text, DECIMAL, MetaData
from sqlalchemy.orm import declarative_base

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