"""
This module defines the Feedback model for managing user feedback on books.

Classes:
- Feedback: Represents user feedback on books with relationships to User and Book.
- FeedbackEnum: Enum for feedback types like 'like' and 'dislike'.

Dependencies:
- SQLAlchemy for ORM and database integration.
"""
from typing import TYPE_CHECKING
from enum import Enum as PyEnum

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr

from app import db

if TYPE_CHECKING:
    from app.models.book import Book
    from app.security.models import User


class FeedbackEnum(PyEnum):
    """
    Enumeration for feedback options.

    This class defines possible feedback types that can be used to express
    sentiments. It provides a controlled set of string constants used for
    determining the type of feedback. This is especially useful in scenarios
    where only predefined feedback options are allowed, ensuring reliable and
    predictable inputs.
    """
    like = "like"  # pylint: disable=invalid-name
    dislike = "dislike"  # pylint: disable=invalid-name


# pylint: disable=too-few-public-methods
class Feedback(db.Model):
    """
    Representation of user feedback on books.

    This class is an ORM model representing user feedback within a database.
    It defines the feedback associated with a specific user and a book,
    utilizing enumerated feedback types. The class establishes relationships
    with the `User` and `Book` models and supports lazy loading for optimized
    database queries. It is mapped to the `feedback` table.

    :ivar id: Unique identifier for the feedback.
    :type id: int
    :ivar user_id: Identifier of the user providing this feedback.
    :type user_id: int
    :ivar book_id: Identifier of the book this feedback pertains to.
    :type book_id: int
    :ivar feedback: The feedback provided by the user, represented as an
        enumeration value.
    :type feedback: FeedbackEnum
    :ivar book: The book entity associated with this feedback, enabling
        a joined relationship for efficient access.
    :type book: Book
    """
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    feedback: Mapped[FeedbackEnum] = mapped_column(Enum(FeedbackEnum))
    book: Mapped["Book"] = relationship(back_populates="feedbacks", lazy="joined")

    @declared_attr
    def user(self) -> Mapped["User"]:
        """
        Provides a relationship attribute mapping the feedback entity to the User entity
        to establish a bidirectional association. The relationship is eager-loaded with
        a joined strategy.

        :return: A mapped relationship to the User entity.
        :rtype: Mapped["User"]
        """
        return relationship("User", back_populates="feedbacks", lazy="joined")
