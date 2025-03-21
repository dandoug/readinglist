from flask_security.models import fsqla_v3 as fsqla

from .. import db

# Define models
fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    pass


class User(db.Model, fsqla.FsUserMixin):
    force_password_change = db.Column(db.Boolean, default=True)
