import base64

from app import db
from app.models import Book


def get_category_bs_tree():
    """
    Generates a bootstrap-compatible tree structure from a given category hierarchy.
    This function first retrieves a category tree and then recursively converts it
    into a tree structure that can be used in applications utilizing bootstrap tree views.

    :rtype: list
    :return: A list representing the bootstrap-compatible tree structure,
        where each element is a dictionary with keys "text" for the category name
        and "nodes" containing any child categories in the same format.
    """
    def _add_categories(cat, context, tree, children):
        fullpath = context + _SEPARATOR + cat if context else cat
        node = {
            "text": cat,
            "state": {"checked": False},
            "fullpath": fullpath,
            "id": _fullpath_to_id(fullpath)
        }
        tree.append(node)
        if children:
            node["nodes"] = []
            for child in children:
                _add_categories(child, fullpath, node["nodes"], children[child])

    categories = _get_category_tree()
    bs_tree = []
    for category in categories:
        _add_categories(category, '', bs_tree, categories[category])
    return bs_tree


def id_to_fullpath(encoded_id):
    """
    Decodes a URL-safe HTML id string back into the original fullpath using Base64.

    The function reverses the transformations applied in `fullpath_to_id`, ensuring
    that the output matches the original input string.

    :param encoded_id: The Base64-encoded URL-safe HTML id string to be decoded.
    :type encoded_id: str
    :return: The original fullpath string.
    :rtype: str
    """
    safe_decoded = (encoded_id
                    .replace('-', '+')
                    .replace('_', '/')
                    .replace('*', '='))
    decoded = base64.b64decode(safe_decoded).decode('utf-8')
    return decoded


def _get_category_list():
    """
    Fetches a list of unique book categories from the database sorted in alphabetical
    order.

    The function establishes a database connection and executes an SQL query to
    retrieve distinct book categories from the database. After
    retrieving the results, the function processes and returns the list of unique
    categories.

    :raises sqlalchemy.exc.SQLAlchemyError: If there is an error executing the
        SQL query or an issue with the database connection.

    :return: A list of strings containing distinct book categories sorted
        alphabetically.
    :rtype: list[str]
    """
    result = (db.session.query(Book.categories_flat)
              .distinct()
              .order_by(Book.categories_flat)
              .all())

    # Extracting the results into a list
    categories = [row.categories_flat for row in result]
    return categories


_SEPARATOR = ' > '   # separator for full category strings


def _get_category_tree():
    """
    Builds a hierarchical tree of categories from a flat list of category strings
    separated by ' > '. Each category string represents a path, where top-level
    categories are separated by '>' from their respective subcategories.

    The function `get_category_tree` iterates through a list of categories to
    construct a nested dictionary structure representing the hierarchical
    relationship among categories. An auxiliary recursive function `_add_categories`
    is used to process each category path and build the tree.

    :raises None: This function does not raise any errors.

    :return: A dictionary where keys are category names and values are nested
        dictionaries representing subcategories.
    :rtype: dict
    """
    def _add_categories(cat, tree, sub_categories):
        if cat not in tree:
            tree[cat] = {}
        if sub_categories:
            # remove first subcategory and make sub_categories list smaller
            sub_category = sub_categories.pop(0)
            _add_categories(sub_category, tree[cat], sub_categories)

    categories = _get_category_list()
    category_tree = {}
    for category in categories:
        categories = category.split(_SEPARATOR)
        top_level_category = categories.pop(0)
        _add_categories(top_level_category, category_tree, categories)
    return category_tree


def _fullpath_to_id(fullpath):
    """
    Converts a fullpath string into a URL-safe HTML id by encoding it using Base64.

    The transformation encodes the input as a Base64 string, replaces URL-sensitive
    characters, and ensures that the resulting id strings are unique and reversible.

    :param fullpath: The original fullpath string to be converted.
    :type fullpath: str
    :return: A URL-safe Base64-encoded HTML id string.
    :rtype: str
    """
    encoded = base64.b64encode(fullpath.encode('utf-8')).decode('utf-8')
    safe_encoded = (encoded
                    .replace('+', '-')
                    .replace('/', '_')
                    .replace('=', '*'))
    return safe_encoded


__all__ = ['get_category_bs_tree', 'id_to_fullpath']
