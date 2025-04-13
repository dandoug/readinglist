"""
This module defines a SQL parsing utility that extracts SQL queries from a script file.

It utilizes an ANTLR-generated MySQL lexer and parser to process SQL scripts and identify
individual queries. The `SQLParser` class reads a SQL script file, parses it into a parse
tree from the root rule, and uses a listener to extract SQL statements.

Classes:
    - SQLParser: Provides functionality to parse a SQL script and extract its queries.
    - _QueryExtractorListener: An internal listener class used to extract queries from
      the parse tree during traversal.

Dependencies:
    - ANTLR4 runtime for Python
    - ANTLR-generated MySQLLexer and MySQLParser
"""
from typing import Iterator, List

from antlr4 import FileStream, CommonTokenStream
from antlr4.tree.Tree import ParseTreeListener, ParseTreeWalker

from tests.integration.sql_parser.grammars.antlr_generated.MySQLLexer import MySQLLexer
from tests.integration.sql_parser.grammars.antlr_generated.MySQLParser import MySQLParser


class SQLParser:  # pylint: disable=too-few-public-methods
    """
    SQLParser is responsible for parsing SQL files and extracting SQL statements.

    The class is used to parse a file containing SQL statements, process it using
    a lexer and parser for MySQL syntax, and extract individual statements. The
    extracted statements can then be iterated over using the provided methods.

    :ivar queries: List of extracted SQL queries from the provided file.
    :type queries: list
    """
    queries: List[str] = []

    def __init__(self, file_path, encoding="utf-8"):
        input_stream = FileStream(file_path, encoding=encoding)
        lexer = MySQLLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = MySQLParser(token_stream)
        tree = parser.root()  # Start parsing from the root rule

        # Use the _QueryExtractorListener to extract queries
        listener = _QueryExtractorListener()
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        # Save the statements we find
        self.queries = listener.get_queries()

    def statements(self) -> Iterator[str]:
        """
        Generates a sequence of queries stored in the object.

        This method serves as a generator that iterates over the `queries` attribute
        of the object. It yields each query from the `queries` sequentially. Used
        for efficiently accessing individual queries without loading all of them
        at once.

        :return: Yields each query from the `queries` attribute in the given object.
        :rtype: Iterator[str]
        """
        yield from self.queries


class _QueryExtractorListener(ParseTreeListener):
    def __init__(self):
        self.queries: List[str] = []

    # noinspection PyPep8Naming
    def enterQuery(self, ctx: MySQLParser.QueryContext):  # pylint: disable=invalid-name
        """
        Extracts and stores the text of each 'query' node when entered.

        This method appends the textual content of a query node to the
        ``queries`` list in the class. It is invoked when the 'query'
        node is entered during the parsing process.

        :param ctx: Context of the currently entered 'query' node from
                    the MySQLParser.
        :type ctx: MySQLParser.QueryContext
        :return: None
        """
        # Extract the text of each 'query' node when entered
        self.queries.append(ctx.getText())

    def get_queries(self) -> list[str]:
        """
        Retrieves a list of stored queries.

        This method returns the collection of queries that are currently stored
        within the instance. The queries are expected to be in the form of strings
        and grouped together in a list.

        :return: A list of queries stored in the instance.
        :rtype: list[str]
        """
        return self.queries
