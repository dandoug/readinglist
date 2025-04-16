"""
This module defines the ReadingStatus and ReadingStatusEnum classes for tracking the 
reading status of users for specific books. It is built using SQLAlchemy and includes 
relationships with User and Book models, and supports statuses like "up_next" and "read".
"""
from typing import TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from app import db

if TYPE_CHECKING:
    from app.models.book import Book
    from app.security.models import User


class ReadingStatusEnum(PyEnum):
    """
    Defines the ReadingStatusEnum class, representing statuses for reading materials.
    
    This enumeration provides distinct statuses for tracking reading progress, such as books 
    that are "up next" or "read". The enum values are stored as strings.
    """
    up_next = "up_next"  # pylint: disable=invalid-name
    read = "read"  # pylint: disable=invalid-name


# pylint: disable=too-few-public-methods
class ReadingStatus(db.Model):
    """
    Represents the reading status of a user for a specific book.

    This model links users with books and tracks their reading status using predefined
    statuses such as "up_next" and "read". Relationships with the User and Book models 
    are also defined for joining and querying related data.
    """
    __tablename__ = "reading_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    status: Mapped[ReadingStatusEnum] = mapped_column(Enum(ReadingStatusEnum))
    book: Mapped["Book"] = relationship(back_populates="reading_statuses", lazy="joined")

    @declared_attr
    def user(self) -> Mapped["User"]:
        """
        Provides a declared attribute `user` representing a relationship to the `User` model.
        The relationship is configured with lazy loading set to "joined" and allows back
        population through the `reading_statuses` field of the `User` model.

        :return: A SQLAlchemy relationship to the associated `User` model
        """
        return relationship("User", back_populates="reading_statuses", lazy="joined")
