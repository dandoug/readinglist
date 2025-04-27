"""
This module defines models and relationships for managing user-created tags and
their associations with books.

Classes:
    - Tag: A user-created tag with a name and an owner and a color,
            containing multiple associated books.
    - TagBook: A many-to-many relationship between tags and books ensuring
            unique associations.

Relationships:
    - A user owns multiple tags.
    - Books can belong to multiple tags, and tags can include multiple books.
"""
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint
from app import db


# pylint: disable=too-few-public-methods
class Tag(db.Model):
    """
    Representation of a Tag model in the database.

    This class represents a tag entity within the database. Each tag is linked to an
    owner (a User) via a foreign key and can have many associated books through a
    many-to-many relationship. It includes a unique constraint to ensure that no two
    tags with the same name exist for the same owner. Instances of this class can
    be used for tracking collections of books by specific users.
    """
    __tablename__ = "tags"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Name of the tag
    name: Mapped[str] = mapped_column(db.String(32), nullable=False)

    # Foreign key to associate the tag with its owner
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    # Color for the tag when displayed visually
    color: Mapped[str] = mapped_column(db.String(32), nullable=False)

    # Unique constraint on (name, owner_id)
    __table_args__ = (UniqueConstraint("name", "owner_id", name="unique_name_per_owner"),)

    # Relationship to the user who owns this tag
    owner: Mapped["User"] = relationship("User", back_populates="tags")  # type: ignore

    # Many-to-many relationship with books
    books: Mapped[list['TagBook']] = relationship('TagBook',
                                                  back_populates='tag',
                                                  cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} name={self.name} " +
            f"color={self.color}>"
            f"owner_id={self.owner_id}>"
        )


# pylint: disable=too-few-public-methods
class TagBook(db.Model):
    """
    Represents the relationship between a tag and a book in the database.

    This class defines the mapping of the relationship between tags and books,
    using their respective IDs. It enforces a unique constraint on the combination
    of tag ID and book ID to ensure that no duplicate relationships exist. The
    class is intended for use with SQLAlchemy's ORM.
    """
    __tablename__ = "tag_books"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key linking to Tag
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)

    # Foreign key linking to Book
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)

    # Relationship linking TagBook to the Tag model
    tag = relationship('Tag', back_populates='books')
    # Relationship assuming a Book model for book-specific information
    book = relationship('Book', back_populates='tags')

    # Unique constraint on (tag_id, book_id) pair
    __table_args__ = (UniqueConstraint("tag_id", "book_id", name="unique_tag_book_pair"),)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} tag_id={self.tag_id} " +
            f"book_id={self.book_id}>"
        )
