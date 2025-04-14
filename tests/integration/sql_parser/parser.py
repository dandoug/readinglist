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

from antlr4 import FileStream, CommonTokenStream, Token
from antlr4.Parser import Parser
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.ErrorStrategy import DefaultErrorStrategy
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
    error_listener = None

    def __init__(self, file_path, encoding="utf-8"):
        input_stream = FileStream(file_path, encoding=encoding)
        lexer = MySQLLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = MySQLParser(token_stream)
        parser._errHandler = _MySQLErrorStrategy()
        self.error_listener = _MySQLCustomErrorListener()
        parser.addErrorListener(self.error_listener)
        tree = parser.queries()  # Start parsing from the root rule

        # Use the _QueryExtractorListener to extract queries
        listener = _QueryExtractorListener(token_stream)
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

    def has_errors(self) -> bool:
        """
        Determines whether there were errors during parsing.
        """
        return self.error_listener.has_errors()

    def get_errors(self):
        """
        Gets the list of errors recorded during parsing.
        """
        return self.error_listener.get_errors()


class _QueryExtractorListener(ParseTreeListener):
    def __init__(self, token_stream: CommonTokenStream):
        self.queries: List[str] = []
        self.token_stream = token_stream  # Save the token stream for reconstructing queries

    # noinspection PyPep8Naming
    def enterQuery(self, ctx: MySQLParser.QueryContext):  # pylint: disable=invalid-name
        """
        Extracts and stores the text of each 'query' node, preserving whitespace.

        This method reconstructs the SQL query from tokens, ensuring that
        the original formatting (like spaces, newlines) is preserved.
        """
        start_token = ctx.start.tokenIndex
        stop_token = ctx.stop.tokenIndex
        # Reconstruct the query text using tokens from the token stream
        tokens = self.token_stream.getTokens(start_token, stop_token)
        query = ''.join(token.text for token in tokens if token.type != Token.EOF)
        self.queries.append(query)

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


class _MySQLErrorStrategy(DefaultErrorStrategy):
    """
    When this method is called, the parser has already decided that it can
    recover by just ignoring the extra token.  In our case, we want to skip the
    big error reporting message if it's only a single semicolon.
    """
    def reportUnwantedToken(self, recognizer: Parser):
        # If the unwanted token is a single semicolon just quietly keep recovering
        if recognizer.getCurrentToken().text == ';':
            return

        # Otherwise generate the big error message
        super().reportUnwantedToken(recognizer)

    def singleTokenDeletion(self, recognizer: Parser):
        # Aggressively delete ; and skip over them.  This handles cases like
        #
        #  /*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
        #  /*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
        #
        # where a file might start with multiple version comments.
        current_token = recognizer.getCurrentToken()
        if current_token.text == ';':
            # consume and discard successive : to get to the next token, i.e. treat
            # multiple semicolons as a single one to delete
            semicolon_token_type = current_token.type
            # while the next token is also a semicolon
            while recognizer.getTokenStream().LA(2) == semicolon_token_type:
                # keep bumping up
                recognizer.consume()
            # At this point, the next token is NOT a semicolon, the current token
            # is a semicolon and the default singleTokenDeletion recovery can handle it

        # Either the current token wasn't a semicolon or we've skipped over repeated semicolons
        return super().singleTokenDeletion(recognizer)


class _MySQLCustomErrorListener(ErrorListener):
    """
    Custom MySQL error listener to capture and store syntax errors during parsing.

    This class extends the `ErrorListener` and is specifically designed to log
    and store syntax errors encountered during the SQL parsing process. It provides
    a mechanism to retrieve and check for the presence of errors after the parsing
    is complete. The errors are stored in a list of dictionaries with details like
    the line, column, message, and offending symbol.
    """
    def __init__(self):
        super().__init__()
        self.errors = []

    # pylint: disable=too-many-arguments
    # pylint: disable=arguments-differ
    # noinspection PyPep8Naming, PyMethodOverriding, PyArgumentListInspection, PyTypeChecker
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        """
        Logs syntax error details and appends the error information to the `errors` list.

        This method is typically invoked when a syntax error occurs during parsing. It
        formats and stores details like the line number, column, offending symbol, and
        error message for further analysis or reporting.
        """
        # Log the error details
        self.errors.append({
            "line": line,
            "column": column,
            "message": msg,
            "offendingSymbol": offendingSymbol.text if offendingSymbol else None
        })

    def has_errors(self) -> bool:
        """
        Determines whether there are any errors in the current context.

        Checks the internal list of errors and returns `True` if there are any
        present, otherwise returns `False`.
        """
        return len(self.errors) > 0

    def get_errors(self):
        """
        Gets the list of errors recorded. This method retrieves a collection of errors, if any,
        that have been accumulated during the execution or operation of the code.
        """
        return self.errors
