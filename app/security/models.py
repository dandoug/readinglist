from flask_security.models import fsqla_v3 as fsqla
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from sqlalchemy.orm import relationship, declared_attr

from .. import db

# Define models
fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    def __repr__(self) -> str:
        return f"{self.name}"


class User(db.Model, fsqla.FsUserMixin):
    @declared_attr
    def reading_statuses(self):
        return relationship("ReadingStatus", back_populates="user")

    @declared_attr
    def feedbacks(self):
        return relationship("Feedback", back_populates="user")

    def __repr__(self) -> str:
        return f"{self.email}"


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_role('admin')
