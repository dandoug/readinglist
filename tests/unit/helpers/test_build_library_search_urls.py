from app.helpers import build_library_search_urls
from app.helpers.utilities import _SEARCH_TEMPLATES

AUTHOR = "Douglas Adams"
TITLE = "The Hitchhiker's Guide to the Galaxy"


def test_build_library_search_urls():
    search_urls = build_library_search_urls(AUTHOR, TITLE)

    assert len(search_urls) == len(_SEARCH_TEMPLATES)
    scc_url = search_urls['Santa Clara Country Library']
    assert scc_url is not None
    assert scc_url.startswith('https://sccl.bibliocommons.com/v2/search?')
    assert 'The+Hitchhiker%27s+Guide+to+the+Galaxy' in scc_url
    assert 'Douglas+Adams' in scc_url