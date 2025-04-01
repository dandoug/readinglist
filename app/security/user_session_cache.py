from flask import session
from flask_login import AnonymousUserMixin
from flask_security.utils import set_request_attr


# Custom user loader that utilizes cache
def custom_user_loader(user_id):
    """Load user, using SimpleCache to store and retrieve the user object."""
    from .. import cache

    # Attempt to retrieve the user from the cache
    user = cache.get(_cache_key_from_string(user_id))
    if user is None:
        # If not in cache, retrieve from datastore and cache it
        user = _load_user_from_datastore(user_id)
        if user:
            cache.set(_cache_key_from_string(user_id), user)
    if user:
        # Set Flask-Security session-related attributes (if any)
        set_request_attr("fs_authn_via", "session")
        set_request_attr("fs_paa", session.get("fs_paa", 0))
    return user


def on_logout(sender, user):
    """Callback for when a user logs out."""
    from .. import cache

    if user:
        # Invalidate the cache for the user
        cache.delete(_cache_key_from_user(user))


def _cache_key_from_string(fs_uniquifier: str):
    return f"user_{fs_uniquifier}"


def _cache_key_from_user(user):
    if isinstance(user, AnonymousUserMixin):
        # Handle the case where the user is not authenticated
        return None
    return _cache_key_from_string(user.fs_uniquifier)


def _load_user_from_datastore(user_id):
    """Loads a user from the datastore if not already cached."""
    from .. import user_datastore

    user = user_datastore.find_user(fs_uniquifier=str(user_id))  # Assumes fs_uniquifier is used for user lookup
    if user and user.active:
        return user
    return None