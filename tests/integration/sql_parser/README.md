# MySQL Parser

The parser in this module is generated using [ANTLR](https://www.antlr.org/index.html).  The parser is used to execute SQL scripts used to setup integration testing.  I originally used a simple hand-coded parser, but it was too brittle and, let's face it, the SQL language with several different comment types and string literals that can contain special characters and statements that span multiple lines is just not that trivial to parse.  I decided that I need a robust parsing tool to do the job.  So, I picked up ANTLR.

Besides, ANTLR is fun to learn about.

It took me awhile to get it right, even using the official MySQL grammar, but I finally made a parser with it that can use the SQL scripts generated straight out of MySqlWorkbench.  So, I'm happy.

## Setup

### Java
ANTLR itself is a Java program, so running it to generate the Python parser code requires a JDK.  Getting that and setting it up to run is beyond the scope of this doc.  The rest of the description here just assumes that there's a `java` executable in your path somewhere.

### ANTLR Tool .jar File

ANTLR is package as a .jar file and is [downloadable](https://www.antlr.org/download.html) from the ANTLR site.  The file used is named something like `antlr-4.13.2-complete.jar` (the current version as of this writing).  The doc below will use `antlr-4.x-complete.jar`, but you should use the latest version available and make necessary adjustments.  

### ANTLR Runtime

Java and .jar file are required at runtime to use the parser that ANTLR produces, but there is a runtime Python module that is required.  It is installed with 

```bash
pip install antlr4-python3-runtime   
```
That's been done for this project and the result has been included in the [requirements.txt](../../../requirements.txt) file already.  So, if you've setup your environment using that, your runtime is all ready.

## Obtain the MySQL Grammar Files

The grammar files are located in the [antlr/grammars-v4](https://github.com/antlr/grammars-v4/tree/master/sql/mysql/Oracle) repository in the `/sql/mysql/Oracle` directory.  Download these files to `grammars`

* [MySQLLexer.g4](https://github.com/antlr/grammars-v4/blob/master/sql/mysql/Oracle/MySQLLexer.g4)
* [MySQLParser.g4](https://github.com/antlr/grammars-v4/blob/master/sql/mysql/Oracle/MySQLParser.g4)

In addition to the grammar files, there are some Python specific files in the [Python3](https://github.com/antlr/grammars-v4/tree/master/sql/mysql/Oracle/Python3) directory.  Download

* [transformGrammar.py](https://github.com/antlr/grammars-v4/blob/master/sql/mysql/Oracle/Python3/transformGrammar.py)

to the `grammars` directory.  And, download the following files

* [MySQLLexerBase.py](https://github.com/antlr/grammars-v4/blob/master/sql/mysql/Oracle/Python3/MySQLLexerBase.py)
* [MySQLParserBase.py](https://github.com/antlr/grammars-v4/blob/master/sql/mysql/Oracle/Python3/MySQLParserBase.py)
* [SqlMode.py](https://github.com/antlr/grammars-v4/blob/master/sql/mysql/Oracle/Python3/SqlMode.py)
* [SqlModes.py](https://github.com/antlr/grammars-v4/blob/master/sql/mysql/Oracle/Python3/SqlModes.py)

to the `grammars/antlr_generated` directory.

## Parser Generation

### Modify Predicates for Python
The grammar files, [MySQLLexer.g4](grammars/MySQLLexer.g4) and [MySQLParser.g4](grammars/MySQLParser.g4), contain  [predicates](https://github.com/antlr/antlr4/blob/dev/doc/predicates.md) that need to be modified slightly to work with Python as the target language.

Run this script
```bash
python transformGrammar.py
```
in the `grammars` directory to make the `.g4` files suitable to produce a Python parser.

### Run ANTLR to generate the parser and lexer

Continuting in the `grammars` directory, run ANTLR to generate the lexer nad parser
```bash
java -jar antlr-4.x-complete.jar -Dlanguage=Python3 -o antlr_generated MySQLLexer.g4 MySQLParser.g4
```
Assumes `java` is in your path somewhere.  Remember to replace `antlr-4.x-complete.jar` with the most recent ANTLR jar (downloaded separately).  This command will generate the lexer and parser Python files into the `antlr_generated` directory.

## Customization

I ran into an issue with the scripts I was using.  MySql has this funky "version comment" syntax like this

```sql
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
```
For my purposes, I don't need the version comment statemnts parsed and skipping them is fine.  However, the semicolon on the end of the lines gets flagged as an "extra" character.   I didn't want to try and hack the grammar in case I downloaded it again later, so I made my own ANTLR error handler to supress the extra `;` issues I was facing.  That looks like this.

```python
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
```

The rest of the customizations were straightforward wrapper things and you can find them in [parser.py](parser.py).

## Usage

The parser is used in the [integration test setup](../conftest.py), like this

```python
def execute_sql_file(db_session, file_path):
    parser = SQLParser(file_path)
    with db_session.cursor() as cursor:  # Use a cursor from the connection
        for statement in parser.statements():
            cursor.execute(statement)
            
    db_session.commit()  # Remember to commit changes
```
and does what I want by executing the statements in a `*.sql` file to setup the database for integration testing.