"""
Validators
"""
import re

import requests
from wtforms.validators import URL, ValidationError


# pylint: disable=too-few-public-methods
class ValidImageUrl(URL):
    """
    Validator to ensure a given URL points to a valid image resource.

    This class extends the functionality of a URL validator to include additional
    checks to verify that the URL points to an actual image resource. It performs
    an HTTP HEAD request to determine if the resource exists and validates
    that the content type is an image format.

    :ivar message: Custom error message to be displayed when validation fails.
    :type message: str
    """
    def __init__(self, message=None):
        super().__init__(require_tld=True, allow_ip=True, message=message)

    def __call__(self, form, field):
        super().__call__(form, field)
        try:
            response = requests.head(field.data, allow_redirects=True, timeout=5)
            content_type = response.headers.get('Content-Type', '')
            if response.status_code != 200 or not content_type.startswith('image/'):
                raise ValidationError(f"{self.message}: {field.data} " +
                                      f"status code: {response.status_code} " +
                                      f"content type: {content_type}")
        except requests.RequestException as e:
            raise ValidationError(f"{self.message}: {field.data}") from e


class ValidAmazonLink(URL):
    """
    WTForms validator that checks if a URL is a valid Amazon book product page.
    Extends the built-in URL validator.
    """
    # Regex for Amazon book product URLs
    amazon_book_pattern = re.compile(
        r'^https?://(www\.)?amazon\.'
        r'(com|co\.uk|ca|de|fr|es|it|nl|se|pl|in|com\.br|com\.mx|com\.au|co\.jp|cn|sg|ae|sa|tr)'
        r'/(?:[^/]+/)?(?:dp|gp/product)/([A-Z0-9]{10})(?:/[^/])*/?[^?]*(?:|\?[^?]*)$',
        re.IGNORECASE
    )

    def __call__(self, form, field):
        # First, run the base URL validator
        super().__call__(form, field)
        url = field.data

        # Now, check for the Amazon book product URL pattern
        if not self.amazon_book_pattern.match(url):
            raise ValidationError(
                f"URL {url} must be a valid Amazon book product page " +
                "(e.g., https://www.amazon.com/dp/XXXXXXXXXX)"
            )
