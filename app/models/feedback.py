from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from enum import Enum as PyEnum

from app import db


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
