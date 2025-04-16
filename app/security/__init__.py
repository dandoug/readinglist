"""
This module initializes the 'registration' blueprint and imports related models, views, and utils.
"""
from app.security.routes import registration_bp, register_admin_views
from app.security.models import Role, User, SecureModelView
from app.security.secure_index_view import SecureAdminIndexView
from app.security.user_session_cache import custom_user_loader, on_logout
from app.security.tag_views import UserTagModelView, tag_pill_markup


__all__ = ['registration_bp', 'register_admin_views', 'Role', 'User', 'SecureModelView',
           'SecureAdminIndexView', 'custom_user_loader', 'on_logout', 'UserTagModelView',
           "tag_pill_markup"]
