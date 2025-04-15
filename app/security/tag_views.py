"""
This module contains Flask-Admin views with custom logic to manage user-specific lists
and their related entities.

Classes:
    UserListModelView: A customized Flask-Admin view to manage "lists" data, ensuring
    only the current user's lists are accessible and editable.

    UserListBookModelView: A customized Flask-Admin view to manage relationships or
    entities linked to user-specific lists.

These views restrict access and query data based on the currently authenticated user,
enforcing user-specific data visibility and preventing unauthorized modifications.
"""
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import abort
from sqlalchemy import func


class UserTagModelView(ModelView):
    """
    A customized Flask-Admin view to manage "tags" data, ensuring only the current user's
    tags are accessible and editable.
    """
    form_excluded_columns = ['owner', 'books']
    column_exclude_list = ['owner', 'books']
    can_edit = True  # Allow editing lists
    can_delete = True  # Allow deleting lists
    # Explicitly specify columns to display in the admin view
    column_list = ["name", "color"]  # Columns to show in the list view
    form_columns = ["name", "color"]  # Columns to show in creation/edit forms

    def is_accessible(self):
        """Ensure that only authenticated users can access this view."""
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        """Redirect or block access if not accessible."""
        abort(403)

    def get_query(self):
        """Restrict the data shown in the admin to only lists owned by the current user."""
        return self.session.query(self.model).filter(self.model.owner_id == current_user.id)

    def get_count_query(self):
        """Restrict the record count for pagination to only the current user's lists."""
        return (self.session.query(func.count())  # pylint: disable=not-callable
                .filter(self.model.owner_id == current_user.id))

    def on_model_change(self, form, model, is_created):
        """
        Ensure that the owner of the list is always the current user.
        This avoids users tampering with the owner field.
        """
        if is_created:
            model.owner_id = current_user.id
        super().on_model_change(form, model, is_created)
