from flask import abort
from flask_admin import expose, AdminIndexView
from flask_security import current_user


class SecureAdminIndexView(AdminIndexView):
    def __init__(self, name=None,
                 endpoint=None, url=None,
                 template='admin/booklist_index.html',
                 menu_class_name=None,
                 menu_icon_type=None,
                 menu_icon_value=None):
        super(SecureAdminIndexView, self).__init__(
            name=name,
            endpoint=endpoint,
            url=url,
            template=template,
            menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type,
            menu_icon_value=menu_icon_value)

    @expose('/')
    def index(self):
        # Check if user is authenticated and has the 'admin' role
        if not current_user.is_authenticated or current_user.has_role('admin') is not True:
            abort(403)  # Return a 403 Forbidden error if not authorized
        return self.render("admin/booklist_index.html")
