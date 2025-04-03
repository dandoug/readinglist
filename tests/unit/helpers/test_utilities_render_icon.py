from app.helpers import render_icon, PLACEHOLDER

ICON_MAPPING = {
    'up_next': 'fa-bookmark',
    'read': 'fa-checkmark'
}

SPAN_ID = 'status-span-123'


def test_render_icon():
    markup = render_icon('up_next', ICON_MAPPING, SPAN_ID)
    assert markup.startswith('<span id="status-span-123">')
    assert markup.endswith('</span>')
    assert '<i class="fa fa-bookmark" aria-hidden="true"></i>' in markup

    markup = render_icon('none', ICON_MAPPING, SPAN_ID)
    assert markup.startswith('<span id="status-span-123">')
    assert markup.endswith('</span>')
    assert PLACEHOLDER in markup