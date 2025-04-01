from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from enum import Enum as PyEnum

from app import db


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
