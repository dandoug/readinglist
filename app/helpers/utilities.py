from flask import url_for
from markupsafe import Markup
from urllib.parse import quote_plus, urlparse, urlunparse

PLACEHOLDER = '<span style="display: inline-block; width: 14px; height: 14px; margin: 0;"></span>'


_SEARCH_TEMPLATES = {
    "Los Gatos Library": "https://losgatos.aspendiscovery.org/Search/Results?join=AND&bool0[]=AND&lookfor0[]={title}&type0[]=Title&lookfor0[]={author}&type0[]=Author&submit=Find",
    "Santa Clara Country Library": "https://sccl.bibliocommons.com/v2/search?custom_edit=false&query=(title%3A({title})%20AND%20contributor%3A({author}))&searchType=bl&suppress=true",
    "San Diego Library": "https://sandiego.bibliocommons.com/v2/search?custom_edit=false&query=(title%3A({title})%20AND%20contributor%3A({author})%20)&searchType=bl&suppress=true",
    "San Diego County Library": "https://sdcl.bibliocommons.com/v2/search?custom_edit=false&query=(anywhere%3A({title})%20AND%20anywhere%3A({author})%20)&searchType=bl&suppress=true",
    "Placer County Library": "https://placer.polarislibrary.com/polaris/search/searchresults.aspx?type=Advanced&term={title}&relation=ALL&by=TI&term2={author}&relation2=ALL&by2=AU&bool1=AND&limit=TOM=*&sort=RELEVANCE&page=0",
    "Nevada County Library": "https://library.nevadacountyca.gov/polaris/search/searchresults.aspx?ctx=1.1033.0.0.1&type=Advanced&term={title}&relation=ALL&by=TI&term2={author}&relation2=ALL&by2=AU&bool1=AND&bool4=AND&limit=(TOM=*%20AND%20OWN=1)&sort=RELEVANCE&page=0&searchid=1"
}


def build_library_search_urls(author, title):
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


def render_icon(item, icon_mapping, span_id):
    # item is the enumeration value (like 'like', 'read'),
    # icon_mapping is a dictionary mapping enum values to font-awesome icons
    if item in icon_mapping:
        return Markup(f'<span id="{span_id}"><i class="fa {icon_mapping[item]}" aria-hidden="true"></i></span>')
    # not in mapping, just use hidden default as a spacer
    return Markup(f'<span id="{span_id}">{PLACEHOLDER}</span>')


def compute_next_url(request):
    return urlparse(request.referrer).path + (
        '?' + urlparse(request.referrer).query if urlparse(request.referrer).query else '') \
        if request.referrer else url_for("index")


# Define a custom function wrapping `urlparse` to parse URLs
def parse_url(url):
    if not url:
        return None
    parsed = urlparse(url)
    return {
        "path": parsed.path,
        "query": parsed.query,
        "full": url
    }



