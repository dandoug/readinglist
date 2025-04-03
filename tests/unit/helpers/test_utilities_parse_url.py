from app.helpers import parse_url

TEST_URL = 'https://booklist.media/search?cat=Q3JpdGljaXNtID4gRXVyb3BlYW4*&cat=Q3JpdGljaXNtID4gRm9sayBUYWxlcw**'


def test_parse_url_normal():
    result = parse_url(TEST_URL)
    assert result['path'] == TEST_URL[TEST_URL.rfind('/'):TEST_URL.index('?')]
    assert result['query'] == TEST_URL.split('?', 1)[1]
    assert result['full'] == TEST_URL


def test_parse_url_none():
    result = parse_url(None)
    assert not result


def test_parse_url_noquery():
    result = parse_url(TEST_URL[0:TEST_URL.index('?')])
    assert result['path'] == TEST_URL[TEST_URL.rfind('/'):TEST_URL.index('?')]
    assert not result['query']
    assert result['full'] == TEST_URL[0:TEST_URL.index('?')]
