
def test_sample_query(db_connection):
    # Query the database to check preloaded data
    with db_connection.cursor() as cursor:
        cursor.execute("SELECT title FROM books WHERE author = 'Sun Tzu'")
        book = cursor.fetchone()

    assert book is not None
    assert book["title"] == "The Art of War"
