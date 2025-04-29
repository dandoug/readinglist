from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, URLField, HiddenField
from wtforms.fields.numeric import DecimalField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, URL

from app.helpers.validators import ValidImageUrl, ValidAmazonLink


class BookForm(FlaskForm):
    # ID field (Optional)
    id = IntegerField("ID", validators=[Optional()])

    # Author (Required)
    author = StringField(
        "Author",
        validators=[
            DataRequired(message="The author is required."),
            Length(max=255, message="The author name cannot exceed 255 characters.")
        ]
    )

    # Title (Required)
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="The title is required."),
            Length(max=255, message="The title cannot exceed 255 characters.")
        ]
    )

    # ASIN (Optional)
    asin = StringField(
        "ASIN",
        validators=[
            Optional(),
            Length(max=20, message="ASIN must not exceed 20 characters.")
        ]
    )

    # Description (Optional)
    book_description = TextAreaField(
        "Description",
        validators=[
            Optional(),
            Length(max=4096, message="The description cannot exceed 4096 characters.")
        ]
    )

    # Rating (Optional but must be between 0 and 5 if provided)
    rating = DecimalField(
        "Rating",
        places=1,
        validators=[
            Optional(),
            NumberRange(min=0, max=5, message="Rating must be between 1 and 5.")
        ],
        filters=[lambda x: float(x) if x else None]  # Converts valid strings to float
    )

    # Book Cover Image URL (Optional but must be a valid URL if provided)
    image = URLField(
        "Cover Image URL",
        validators=[
            Optional(),
            ValidImageUrl(message="Must be a valid image URL.")
        ]
    )

    # Amazon Purchase URL (Optional but must be a valid URL if provided)
    link = URLField(
        "Amazon URL",
        validators=[
            Optional(),
            ValidAmazonLink()
        ]
    )

    # Categories, required)
    categories_flat = StringField(
        "Categories",
        validators=[
            DataRequired(message="The category string is required."),
            Length(max=255,
                   message="The category string is ' > ' separated and cannot exceed 255 chars.")
        ]
    )

    # Pages (Optional but must be positive)
    hardcover = StringField(
        "Pages",
        validators=[
            Optional(),
            Length(max=64, message="Pages string must not exceed 64 characters.")
        ]
    )

    # ISBN-10 (Optional)
    isbn_10 = StringField(
        "ISBN-10",
        validators=[
            Optional(),
            Length(max=13, message="ISBN-10 must not exceed 13 characters.")
        ]
    )

    # ISBN-13 (Optional, 13 characters)
    isbn_13 = StringField(
        "ISBN-13",
        validators=[
            Optional(),
            Length(max=17, message="ISBN-13 must not exceed 13 characters.")
        ]
    )

    # Bestsellers Rank (Optional)
    bestsellers_rank_flat = TextAreaField(
        "Bestsellers Rank",
        validators=[
            Optional(),
            Length(max=4096, message="Bestsellers Rank cannot exceed 4096 characters.")
        ]
    )

    # Specifications (Optional)
    specifications_flat = TextAreaField(
        "Specifications",
        validators=[
            Optional(),
            Length(max=4096, message="Specifications cannot exceed 4096 characters.")
        ]
    )

    # Next (Hidden Field)
    next = HiddenField("next")

    def fill_from_book(self, book):
        """
            Populate the form fields from a Book object.
        """
        self.title.data = book.title
        self.author.data = book.author
        self.book_description.data = book.book_description
        self.specifications_flat.data = book.specifications_flat
        self.asin.data = book.asin
        self.bestsellers_rank_flat.data = book.bestsellers_rank_flat
        self.categories_flat.data = book.categories_flat
        self.hardcover.data = book.hardcover
        self.image.data = book.image
        self.isbn_10.data = book.isbn_10
        self.isbn_13.data = book.isbn_13
        self.link.data = book.link
        self.rating.data = book.rating
