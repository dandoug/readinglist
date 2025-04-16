"""
This module contains Flask-Admin views with custom logic to manage user-specific lists
and their related entities.

Classes:
    UserListModelView: A customized Flask-Admin view to manage "lists" data, ensuring
    only the current user's lists are accessible and editable.

    UserListBookModelView: A customized Flask-Admin view to manage relationships or
    entities linked to user-specific lists.

These views restrict access and query data based on the currently authenticated user,
enforcing user-specific data visibility and preventing unauthorized modifications.
"""
import re

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import abort
from sqlalchemy import func
from wtforms.fields.choices import SelectField
from wtforms.widgets import html_params


from app.config import PROJECT_ROOT

COLOR_SCSS_PATH = PROJECT_ROOT / 'app/static/scss/badge-color.scss'


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


def _get_color_choices() -> list[tuple[str, str]]:
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


# pylint: disable=too-few-public-methods
class BootstrapSelectWidget:
    """
    Widget class for rendering a custom Bootstrap-styled <select> element.

    This class provides a styled dropdown widget compatible with Bootstrap's
    `selectpicker` component. It ensures proper integration with Bootstrap's
    styling and additional optional attributes like `data-live-search`. The
    widget allows customization and renders options with badges for better
    UI experience.
    """
    def __call__(self, field, **kwargs):
        # Ensure the `selectpicker` class is merged into the final `class` attribute
        existing_classes = kwargs.get('class', '')
        kwargs['class'] = f"{existing_classes} selectpicker form-control".strip()

        # Optionally add other attributes (e.g., data-live-search)
        kwargs.setdefault('data-live-search', 'true')

        html = [f'<select {html_params(id=field.id, name=field.name, **kwargs)}>']

        # Loop through the 2-tuple (value, label) choices
        for value, label in field.choices:
            data_content = f"<span class='badge badge-pill badge-{value}'>{label}</span>"

            # Check if this choice is the current/selected value
            selected_html = 'selected' if field.data == value else ''

            # Render the `<option>` tag with `data-content` and selection logic
            html.append(f'<option value="{value}" data-content="{data_content}"' +
                        f' {selected_html}>{label}</option>')

        html.append('</select>')
        return ''.join(html)  # Return the constructed HTML as a string


class UserTagModelView(ModelView):
    """
    A customized Flask-Admin view to manage "tags" data, ensuring only the current user's
    tags are accessible and editable.
    """
    form_excluded_columns = ['owner', 'books']
    column_exclude_list = ['owner', 'books']

    # Explicitly specify columns to display in the admin view
    column_list = ["name", "color"]  # Columns to show in the list view
    form_columns = ["name", "color"]  # Columns to show in creation/edit forms
    form_overrides = {
        'color': SelectField
    }
    form_args = {
        'color': {
            'choices': _get_color_choices(),  # Dynamically provide choices
            'widget': BootstrapSelectWidget()  # Use the custom widget for badge-pill rendering
        }
    }

    can_edit = True  # Allow editing lists
    can_delete = True  # Allow deleting lists
    edit_template = 'tag_edit.html'

    def on_form_prefill(self, form, _id):
        # Dynamically set choices for color field
        form.color.choices = _get_color_choices()

    def validate_form(self, form):
        form.color.choices = _get_color_choices()
        return super().validate_form(form)

    def is_accessible(self):
        """Ensure that only authenticated users can access this view."""
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        """Redirect or block access if not accessible."""
        abort(403)

    def get_query(self):
        """Restrict the data shown in the admin to only lists owned by the current user."""
        return self.session.query(self.model).filter(self.model.owner_id == current_user.id)

    def get_count_query(self):
        """Restrict the record count for pagination to only the current user's lists."""
        return (self.session.query(func.count())  # pylint: disable=not-callable
                .filter(self.model.owner_id == current_user.id))

    def on_model_change(self, form, model, is_created):
        """
        Ensure that the owner of the list is always the current user.
        This avoids users tampering with the owner field.
        """
        if is_created:
            model.owner_id = current_user.id
        super().on_model_change(form, model, is_created)
