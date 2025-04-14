"""
This module defines models and relationships for managing user-created lists and their 
associations with books.

Classes:
    - List: A user-created list with a name and an owner, containing multiple associated books.
    - ListBook: A many-to-many relationship between lists and books ensuring unique associations.

Relationships:
    - A user owns multiple lists.
    - Books can belong to multiple lists, and lists can include multiple books.
"""
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint
from app import db


# pylint: disable=too-few-public-methods
class List(db.Model):
    """
    Representation of a List model in the database.

    This class represents a list entity within the database. Each List is linked to an
    owner (a User) via a foreign key and can have many associated books through a
    many-to-many relationship. It includes a unique constraint to ensure that no two
    lists with the same name exist for the same owner. Instances of this class can
    be used for tracking collections of books by specific users.

    :ivar id: Primary key identifier for the List.
    :type id: int
    :ivar name: The name of the List.
    :type name: str
    :ivar owner_id: Foreign key identifier that connects the List to its owner.
    :type owner_id: int
    :ivar owner: The User who owns the List. This is a relationship property.
    :type owner: User
    :ivar books: A collection of Book instances associated with this List.
    :type books: list[Book]
    """
    __tablename__ = "lists"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Name of the list
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)

    # Foreign key to associate the list with its owner
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    # Unique constraint on (name, owner_id)
    __table_args__ = (UniqueConstraint("name", "owner_id", name="unique_name_per_owner"),)

    # Relationship to the user who owns this list
    owner: Mapped["User"] = relationship("User", back_populates="lists")  # type: ignore

    # Many-to-many relationship with books
    books: Mapped[list["Book"]] = relationship(    # type: ignore
        "Book",
        secondary="list_books",
        primaryjoin="List.id == ListBook.list_id",
        secondaryjoin="Book.id == ListBook.book_id",
        back_populates="lists"
    )

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} name={self.name} "
            f"owner_id={self.owner_id}>"
        )


# pylint: disable=too-few-public-methods
class ListBook(db.Model):
    """
    Represents the relationship between a list and a book in the database.

    This class defines the mapping of the relationship between lists and books,
    using their respective IDs. It enforces a unique constraint on the combination
    of list ID and book ID to ensure that no duplicate relationships exist. The
    class is intended for use with SQLAlchemy's ORM.

    :ivar id: Unique identifier for the ListBook relationship.
    :type id: int
    :ivar list_id: Identifier of the list to which this relationship belongs.
    :type list_id: int
    :ivar book_id: Identifier of the book in this relationship.
    :type book_id: int
    """
    __tablename__ = "list_books"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key linking to List
    list_id: Mapped[int] = mapped_column(ForeignKey("lists.id", ondelete="CASCADE"), nullable=False)

    # Foreign key linking to Book
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)

    # Unique constraint on (list_id, book_id) pair
    __table_args__ = (UniqueConstraint("list_id", "book_id", name="unique_list_book_pair"),)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} list_id={self.list_id} " +
            f"book_id={self.book_id}>"
        )
