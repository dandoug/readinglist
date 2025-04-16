"""
Utility programs used to generate tag color palette
"""
from pprint import pprint

import requests

# Starting point of 20 colors and the contrast colors I got from https://colorkit.co/
COLORS = [
    {"color": "#413344", "contrast_color": "#bdbbbd"},
    {"color": "#614c65", "contrast_color": "#bebabf"},
    {"color": "#806485", "contrast_color": "#f6e3f9"},
    {"color": "#936397", "contrast_color": "#ffebff"},
    {"color": "#a662a8", "contrast_color": "#fff4ff"},
    {"color": "#664972", "contrast_color": "#c1b9c4"},
    {"color": "#463c57", "contrast_color": "#bdbbc0"},
    {"color": "#6e8da9", "contrast_color": "#ffffff"},
    {"color": "#91bcdd", "contrast_color": "#445a6b"},
    {"color": "#567d99", "contrast_color": "#f1ffff"},
    {"color": "#395e77", "contrast_color": "#adbfce"},
    {"color": "#305662", "contrast_color": "#b7bcbe"},
    {"color": "#264d4d", "contrast_color": "#b8bdbc"},
    {"color": "#315c45", "contrast_color": "#b4beb8"},
    {"color": "#8a9a65", "contrast_color": "#ffffff"},
    {"color": "#b6b975", "contrast_color": "#57592c"},
    {"color": "#b65d54", "contrast_color": "#ffebdf"},
    {"color": "#b60033", "contrast_color": "#e1afb7"},
    {"color": "#98062d", "contrast_color": "#d8b2b8"},
    {"color": "#800022", "contrast_color": "#d3b4b9"}
]

COLOR_API_URL_TEMPLATE = "https://www.thecolorapi.com/id?hex={hex_code}&format=JSON"


def build_color_list_with_names() -> list[dict]:
    """
    Builds a list of colors with their names fetched from an external API.

    This function iterates through a predefined list of colors, sends a GET
    request to an external API for obtaining the name of each color based
    on its hexadecimal code, and adds the color name to the color's
    dictionary representation. If the request fails for a color, the
    function skips that color and logs the failure.

    :return: A list of dictionaries containing colors with their respective names.
    :rtype: list[dict]
    """
    result = []
    for color in COLORS:
        hex_code = color["color"].replace("#", "")
        response = requests.get(COLOR_API_URL_TEMPLATE.format(hex_code=hex_code), timeout=30)
        if response.status_code == 200:
            color_name = response.json()["name"]["value"]
            # lower case and remove spaces
            color_name = color_name.lower().replace(" ", "-")
            color["name"] = color_name
            result.append(color)
        else:
            print(f"Bad response for color {hex_code}.  Response: {response.text}  Skipping")

    return result


if __name__ == "__main__":
    update_colors = build_color_list_with_names()
    pprint(update_colors)
