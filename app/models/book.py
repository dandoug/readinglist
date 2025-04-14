from sqlalchemy.orm import Mapped, mapped_column, relationship
from .reading_status import ReadingStatus
from .feedback import Feedback
from .lists import ListBook
from app import db


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

    # Relationship to ListBook, connects with ListBook.book
    lists: Mapped[list['ListBook']] = relationship('ListBook',
                                                   back_populates='book',
                                                   cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        """Converts the model instance into a dictionary."""
        result =  {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if result.get('book_description'):
            # some descriptions have &nbsp; and these need to be rendered as just space
            result['book_description'] = result['book_description'].replace('\u00A0', '\u0020')
        return result

    def __repr__(self) -> str:
        """Provides a clean string representation of the object."""
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"


__all__ = ["Book"]
