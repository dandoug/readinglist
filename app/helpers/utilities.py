"""
This module provides utilities for building library search URLs, rendering icons, URL parsing,
and computing navigation paths. It includes helper functions for escaping user input, mapping
values to icons, and handling request referrer URLs.
"""
from urllib.parse import quote_plus, urlparse

import bleach
from flask import url_for
from markupsafe import Markup

PLACEHOLDER = '<span class="placeholder-icon"></span>'


_SEARCH_TEMPLATES = {
    "Los Gatos Library":
        "https://losgatos.aspendiscovery.org/Search/Results?join=AND&bool0[]=AND&lookfor0[]=" +
        "{title}&type0[]=Title&lookfor0[]={author}&type0[]=Author&submit=Find",
    "Santa Clara Country Library":
        "https://sccl.bibliocommons.com/v2/search?custom_edit=false&query=(title%3A({title})" +
        "%20AND%20contributor%3A({author}))&searchType=bl&suppress=true",
    "San Diego Library":
        "https://sandiego.bibliocommons.com/v2/search?custom_edit=false&query=(title%3A({title})" +
        "%20AND%20contributor%3A({author})%20)&searchType=bl&suppress=true",
    "San Diego County Library":
        "https://sdcl.bibliocommons.com/v2/search?custom_edit=false&query=(anywhere%3A({title})" +
        "%20AND%20anywhere%3A({author})%20)&searchType=bl&suppress=true",
    "Placer County Library":
        "https://placer.polarislibrary.com/polaris/search/searchresults.aspx?type=Advanced" +
        "&term={title}&relation=ALL&by=TI&term2={author}&relation2=ALL&by2=AU&bool1=AND" +
        "&limit=TOM=*&sort=RELEVANCE&page=0",
    "Nevada County Library":
        "https://library.nevadacountyca.gov/polaris/search/searchresults.aspx?ctx=1.1033.0.0.1" +
        "&type=Advanced&term={title}&relation=ALL&by=TI&term2={author}&relation2=ALL&by2=AU" +
        "&bool1=AND&bool4=AND&limit=(TOM=*%20AND%20OWN=1)&sort=RELEVANCE&page=0&searchid=1"
}


def build_library_search_urls(author, title) -> dict[str, str]:
    """
    Builds library search URLs using the given author and title.

    This function takes the author's name and the title of a work, escapes
    them to make them URL-safe, and substitutes them into predefined search
    URL templates. The result is a dictionary of search URLs for external
    library systems or online catalog platforms.

    :param author: The name of the author to search for (must be a string).
    :type author: str
    :param title: The title of the work to search for (must be a string).
    :type title: str
    :return: A dictionary where the keys are search platform identifiers
             and the values are URLs with the provided author and title
             embedded within them.
    :rtype: dict
    """
    escaped_title = quote_plus(title, safe="")
    escaped_author = quote_plus(author, safe="")
    search_urls = {
        key: value.replace("{title}", escaped_title).replace("{author}", escaped_author)
        for key, value in _SEARCH_TEMPLATES.items()
    }
    return search_urls


def render_icon(item, icon_mapping, span_id) -> Markup:
    """
    Render an HTML span element with an icon based on the given item and mapping.

    This function generates a span element containing a font-awesome icon
    corresponding to the provided item. The icon is determined by the
    ``icon_mapping`` dictionary. If the item is not found in the ``icon_mapping``,
    a default hidden placeholder HTML element is returned as a spacer.

    :param item: The enumeration value representing the action (e.g., 'like', 'read')
                 to map to a corresponding icon.
    :type item: str
    :param icon_mapping: A dictionary mapping enumeration values to font-awesome icon
                         classes.
    :type icon_mapping: dict
    :param span_id: The ID attribute to assign to the span element in the resultant
                    HTML string.
    :type span_id: str
    :return: A `Markup` object containing the rendered span element string
             with the appropriate icon or a placeholder if the item is not mapped.
    :rtype: Markup
    """
    # item is the enumeration value (like 'like', 'read'),
    # icon_mapping is a dictionary mapping enum values to font-awesome icons
    if item in icon_mapping:
        return Markup(  # nosec B704
            f'<span id="{span_id}">' +
            f'<i class="fa {icon_mapping[item]}" aria-hidden="true"></i>' +
            '</span>'
        )
    # not in mapping, just use hidden default as a spacer
    return Markup(f'<span id="{span_id}">{PLACEHOLDER}</span>')  # nosec B704


def compute_next_url(request):
    """
    Compute the next URL based on the referrer of the provided request object.

    This function examines the `referrer` attribute of the given `request` object
    to compute the next URL to navigate to. If the `request` contains a valid `referrer`,
    the function extracts the path and appends the query string (if present). If no
    `referrer` is available, the function defaults to returning the URL for the
    "index" route.

    :param request: The request object containing information about the current
        HTTP request. Should include a `referrer` attribute to extract navigation
        information from.
    :type request: flask.Request
    :return: The computed next URL string based on the `referrer`, or the default
        URL for the "index" route if no `referrer` is present.
    :rtype: str
    """
    return urlparse(request.referrer).path + (
        '?' + urlparse(request.referrer).query if urlparse(request.referrer).query else '') \
        if request.referrer else url_for("index")


# Define a custom function wrapping `urlparse` to parse URLs
def parse_url(url):
    """
    Parses a given URL string and extracts its components.

    This function takes a URL string as input, validates its presence, and
    parses it using Python's `urlparse` module. It extracts the path and query
    components and provides them along with the full URL in a dictionary format.

    :param url: The URL string to be parsed.
    :type url: str
    :return: A dictionary containing the parsed components: "path", "query",
        and the original "full" URL string. Returns None if the input URL is
        not provided.
    :rtype: dict or None
    """
    if not url:
        return None
    parsed = urlparse(url)
    return {
        "path": parsed.path,
        "query": parsed.query,
        "full": url
    }


def sanitize(content):
    """
    Strip all HTML content from the input string.

    :param content: The content to sanitize
    :return: Plain text with all HTML tags removed
    """
    if content is None or not isinstance(content, str):
        return content

    # Strip all HTML tags by setting allowed_tags to an empty list
    return bleach.clean(
        content,
        tags=[],  # No HTML tags allowed
        attributes={},  # No attributes allowed
        strip=True  # Strip all disallowed tags (which is all tags)
    )


def sanitize_categories_flat(categories: str):
    """
    Clean the component pieces of a falt categories string.
    :param categories:
    :return:
    """
    cat_strings = categories.split(' > ')
    sanitize_list = []
    for cat in cat_strings:
        sanitize_list.append(sanitize(cat))
    return ' > '.join(sanitize_list)
