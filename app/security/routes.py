from flask import current_app as app, request, render_template, redirect, after_this_request
from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_login import login_required
from flask_security import roles_required
from flask_security.forms import build_form_from_request
from flask_security.registerable import register_user, register_existing
from flask_security.utils import view_commit, get_post_register_redirect, config_value as cv
from flask_sqlalchemy import SQLAlchemy

from . import registration_bp
from .models import SecureModelView, User, Role


class UserModelView(SecureModelView):
    can_create = False
    column_list = ['email', 'confirmed_at', 'active', 'roles']
    form_columns = ['email', 'confirmed_at', 'active', 'roles']

    def create_view(self):
        # Redirect to the /register page
        return redirect("/register")
    list_template = 'security/list_user.html'
    edit_template = 'security/edit_user.html'


class RoleModelView(SecureModelView):
    column_list = ['name', 'description']
    form_columns = ['name', 'description', 'users']


def register_admin_views(db: SQLAlchemy, admin: Admin):
    admin.add_link(MenuLink(name='Home', url='/'))
    admin.add_view(UserModelView(User, db.session))
    admin.add_view(RoleModelView(Role, db.session))


@registration_bp.route('/register', methods=['GET', 'POST'])
@login_required  # Ensure only logged-in users can access
@roles_required('admin')  # Restrict to users with the 'admin' role
def custom_register():
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
