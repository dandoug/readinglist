"""
Defines database models and admin views for authentication and role management.

This module includes models for users and roles, integrating with Flask-Security 
and Flask-Admin for authentication and role-based access control. It also provides
a custom admin view enforcing restricted access to authorized administrators only.

Classes:
    Role: Represents a user role in the application with specific permissions.
    User: Represents an application user with role associations and relationships.
    SecureModelView: A custom admin view with access restricted to 'admin' users.
"""
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask_security.models import fsqla_v3 as fsqla
from sqlalchemy.orm import relationship, declared_attr

from app import db

# Define models
fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    """
    Represents the roles a user can have in the application.

    Each role defines a set of permissions or access levels
    assigned to users for role-based authentication.
    """

    def __repr__(self) -> str:
        return f"{self.name}"


class User(db.Model, fsqla.FsUserMixin):
    """
    Represents a user in the application with authentication and role information.

    A user can have multiple relationships such as reading statuses and feedbacks,
    allowing association with various entities in the application.
    """

    @declared_attr
    def reading_statuses(self):
        """
        Defines a property for accessing the reading statuses associated with the user.

        The property is declared as a SQLAlchemy relationship, linking the current
        user to their respective reading statuses. This property facilitates
        bidirectional association and interaction between the user and the
        ReadingStatus model.

        :return: A SQLAlchemy relationship object linking the user with their
            reading statuses.
        :rtype: sqlalchemy.orm.relationship
        """
        return relationship("ReadingStatus", back_populates="user")

    @declared_attr
    def feedbacks(self):
        """
        Represents the relationship between the current model and the "Feedback" model.

        This property defines a relationship, where the "Feedback" model is connected
        to the current model and can be accessed through the `user` attribute of
        "Feedback". It uses the SQLAlchemy `relationship` function to establish this
        link with bidirectional behavior.

        :return: A SQLAlchemy relationship configured with "Feedback" as the related model.
        :rtype: sqlalchemy.orm.relationship
        """
        return relationship("Feedback", back_populates="user")

    # Relationship to lists owned by the user
    @declared_attr
    def lists(self):
        """
        Provides a declared attribute for relationship with the 'List' model.

        This attribute enables the establishment of a relationship between the current
        model and the 'List' model, defining how they are interconnected in the database
        or ORM (Object-Relational Mapping) structure.

        :return: A SQLAlchemy relationship between this model and the 'List' model.
        :rtype: sqlalchemy.orm.relationship
        """
        return relationship("List", back_populates="owner")

    def __repr__(self) -> str:
        """
        Provides a string representation of the instance for debugging
        and logging purposes. The returned string is a concise,
        format that includes the email attribute.

        :return: A string representing the instance, primarily including
            the email attribute.
        :rtype: str
        """
        return f"{self.email}"


class SecureModelView(ModelView):
    """
    Custom model view that adds security measures by restricting access to administrators.

    The view ensures only authenticated users with the 'admin' role can access
    the underlying functionality.
    """

    def is_accessible(self):
        """
        Checks if the current user is authenticated and has the 'admin' role.

        :return: True if the current user can access this view, otherwise False.
        :rtype: bool
        """
        return current_user.is_authenticated and current_user.has_role('admin')
