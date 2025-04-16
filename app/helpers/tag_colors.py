"""
Extracts and manages badge color definitions from SCSS files for tag styling and customization.

This module provides functionality to parse and cache color definitions from SCSS files, making them
available for use in tag-related features throughout the application.
"""
import re
from functools import lru_cache

from app.helpers.buildinfo import PROJECT_ROOT

COLOR_SCSS_PATH = PROJECT_ROOT / 'app/static/scss/badge-color.scss'


@lru_cache(maxsize=1)
def get_color_choices() -> list[tuple[str, str]]:
    """
    Generates a list of color choices derived from SCSS badge colors.

    This function extracts badge colors from SCSS and formats them as a list
    of tuples. Each tuple contains the raw name of the color and a user-friendly
    formatted version of the name.
    """
    colors = _get_badge_colors_from_scss()
    result = []
    for name in colors:
        readable_name = name.replace("_", " ").title()
        result.append((name, readable_name))
    return result


def _get_badge_colors_from_scss() -> dict[str, dict[str, str]]:
    """
    Extracts badge color mappings from a SCSS file. Parses defined color mappings
    from SCSS `$badge-colors` map. The SCSS file is expected to have a `$badge-colors`
    map definition that includes badge names and their respective "color" and
    "contrast_color" properties.
    """
    with open(COLOR_SCSS_PATH, 'r', encoding='utf-8') as file:
        scss_content = file.read()

    badge_colors_pattern = r"\$badge-colors:\s*\((.*?)\);\n"
    match = re.search(badge_colors_pattern, scss_content, re.S)

    if not match:
        raise ValueError("Cannot find $badge-colors in the SCSS file")

    map_body = match.group(1).strip()

    color_pattern = re.compile(
        r'([\w-]+):\s*\("color":\s*(#[0-9a-fA-F]+),\s*"contrast_color":\s*(#[0-9a-fA-F]+)\)')
    badge_colors = {}

    for line in map_body.splitlines():
        match = color_pattern.search(line)
        if match:
            name, color, contrast_color = match.groups()
            badge_colors[name] = {"color": color, "contrast_color": contrast_color}

    return badge_colors
