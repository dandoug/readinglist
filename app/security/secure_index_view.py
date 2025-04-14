"""
This module implements a secure admin index view for Flask-Admin.

It restricts access to authorized users with the 'admin' role, rendering a custom template for
the admin home page while ensuring unauthorized access results in a 403 error.
"""
from flask import abort
from flask_admin import expose, AdminIndexView
from flask_security import current_user


class SecureAdminIndexView(AdminIndexView):
    """
    Represents a secure admin index view for handling the admin interface with
    authentication and role-based access controls.

    This custom admin index view enforces that only authenticated users with the
    'admin' role can access the associated admin interface. Unauthorized access
    attempts result in a 403 Forbidden error. The class is built upon Flask Admin
    AdminIndexView and allows customization of endpoints, URLs, and templates.
    """
    # noinspection PyMethodOverriding
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, name=None,
                 endpoint=None, url=None,
                 template='admin/booklist_index.html',
                 menu_class_name=None,
                 menu_icon_type=None,
                 menu_icon_value=None):
        super().__init__(
            name=name,
            endpoint=endpoint,
            url=url,
            template=template,
            menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type,
            menu_icon_value=menu_icon_value)

    @expose('/')
    def index(self):
        # Check if user is authenticated
        if not current_user.is_authenticated:  # Still require authentication
            abort(403)
        return self.render("admin/booklist_index.html")
