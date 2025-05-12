from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)


def add_limits_to_views(app):
    # Add limits specifically to the Flask-Login `/login` route
    limiter.limit("10 per minute", key_func=get_remote_address)(app.view_functions["security.login"])
