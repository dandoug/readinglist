from pathlib import Path

from tests.integration.sql_parser.parser import SQLParser

# Calculate the path to where the SQL files are
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # Navigate to the project root
DATABASE_DIR = PROJECT_ROOT / "database"


def test_sql_parser():
    files = ["create-tables.sql", "initial-books-load.sql"]
    for file in files:
        sql_file = DATABASE_DIR / file
        assert sql_file.exists()

        print(f"\n\nParsing {sql_file}...")
        parser = SQLParser(sql_file)
        assert parser.has_errors() is False
        cnt = 0
        for statement in parser.statements():
            cnt += 1
            print(f">>> {statement}")
        assert cnt > 0
