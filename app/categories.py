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