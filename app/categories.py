from sqlalchemy import text


def get_category_list():
    """
    Fetches a list of unique book categories from the database sorted in alphabetical
    order.

    The function establishes a database connection and executes an SQL query to
    retrieve distinct book categories from the `readinglist.books` table. After
    retrieving the results, the function processes and returns the list of unique
    categories.

    :raises sqlalchemy.exc.SQLAlchemyError: If there is an error executing the
        SQL query or an issue with the database connection.

    :return: A list of strings containing distinct book categories sorted
        alphabetically.
    :rtype: list[str]
    """
    from app import db
    with db.engine.connect() as conn:
        result = conn.execute(
            text("SELECT distinct categories_flat FROM readinglist.books order by categories_flat;"))
    categories = []
    for row in result:
        categories.append(row.categories_flat)
    return categories


def get_category_tree():
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

    categories = get_category_list()
    category_tree = {}
    for category in categories:
        categories = category.split(' > ')
        top_level_category = categories.pop(0)
        _add_categories(top_level_category, category_tree, categories)
    return category_tree


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
    def _add_categories(cat, tree, children):
        node = {
            "text": cat,
            "state": {"checked": False}
        }
        tree.append(node)
        if children:
            node["nodes"] = []
            for child in children:
                _add_categories(child, node["nodes"], children[child])

    categories = get_category_tree()
    bs_tree = []
    for category in categories:
        _add_categories(category, bs_tree, categories[category])
    return bs_tree


__all__ = ['get_category_list', 'get_category_tree', 'get_category_bs_tree']
