"""
This module handles user registration, role-based access, and admin functionality.

It defines custom views for managing users and roles using Flask-Admin, enforces security 
permissions, and manages registration workflows. Admin utilities include user and role 
management, menu links, and secure endpoints. This module also defines a route for the 
custom registration page accessible only to admin users.

Classes:
- UserModelView: Custom admin view for user management.
- RoleModelView: Custom admin view for role management.

Functions:
- register_admin_views: Registers admin views and appends custom menu links.
- custom_register: Handles user registration for admin users.

Dependencies:
- Flask, Flask-Admin, Flask-Security modules for routing and security features.
- Flask-SQLAlchemy for database integration.
"""
from flask import request, render_template, redirect, after_this_request, Blueprint
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_login import login_required
from flask_security import roles_required
from flask_security.forms import build_form_from_request
from flask_security.registerable import register_user, register_existing
from flask_security.utils import view_commit, get_post_register_redirect, config_value as cv
from flask_sqlalchemy import SQLAlchemy
from app.security.models import SecureModelView, User, Role


registration_bp = Blueprint('registration', __name__)


class UserModelView(SecureModelView):
    """
    Provides a customized view for managing user models within a secure
    administrative interface. This view restricts the creation of new users
    and customizes the templates for listing and editing users.
    """
    can_create = False
    column_list = ['email', 'confirmed_at', 'active', 'roles']
    form_columns = ['email', 'confirmed_at', 'active', 'roles']

    def create_view(self):
        # Redirect to the /register page
        return redirect("/register")
    list_template = 'security/list_user.html'
    edit_template = 'security/edit_user.html'


class RoleModelView(SecureModelView):
    """
    Represents the RoleModelView class, which extends SecureModelView for managing
    roles in an administrative interface.

    The class provides functionality to display and manage data related to roles
    such as their names, descriptions, and associated users. It specifies columns
    to be displayed in lists and forms for user interaction.
    """
    column_list = ['name', 'description']
    form_columns = ['name', 'description', 'users']


def register_admin_views(db: SQLAlchemy, admin: Admin):
    """
    Registers views and menu links to the Flask-Admin interface.

    This function integrates specified model views and additional menu links
    into your Flask-Admin interface, allowing administrators to manage
    database entities and access custom links conveniently.

    :param db: The SQLAlchemy database instance used for database operations.
    :type db: SQLAlchemy
    :param admin: The Flask-Admin instance to which the views and links will
        be added.
    :type admin: Admin
    :return: None
    """
    admin.add_link(MenuLink(name='About', url='/about'))
    admin.add_link(MenuLink(name='Home', url='/'))
    admin.add_view(UserModelView(User, db.session))
    admin.add_view(RoleModelView(Role, db.session))


@registration_bp.route('/register', methods=['GET', 'POST'])
@login_required  # Ensure only logged-in users can access
@roles_required('admin')  # Restrict to users with the 'admin' role
def custom_register():
    """
    Handles user registration functionality.

    This function is associated with the '/register' endpoint and allows users with
    the 'admin' role to register new users. It supports both GET and POST methods.
    The function utilizes a form generated based on the request. On successful form
    submission via POST, a new user is registered, and the system redirects to a
    post-registration URL. In the case of a GET request or a failure to validate the
    form, the registration template is rendered for further input.

    :parameters:
        No parameters are passed explicitly to this function, as it is tied to an
        HTTP endpoint and handles the request context internally.

    :return:
        A redirect to a post-registration URL upon successful user registration, or
        renders the registration template with the form for further input when a
        GET request is made or validation fails.

    """
    form = build_form_from_request("register_form")
    if request.method == 'POST' and form.validate_on_submit():
        after_this_request(view_commit)
        user = register_user(form)
        form.user = user

        return redirect(get_post_register_redirect())

    # Here on GET or failed validate
    if request.method == "POST" and cv("RETURN_GENERIC_RESPONSES"):
        gr = register_existing(form)
        if gr:
            return redirect(get_post_register_redirect())

    # Get
    return render_template(cv("REGISTER_USER_TEMPLATE"), register_user_form=form)
