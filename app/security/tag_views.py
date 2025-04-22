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

from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import abort
from markupsafe import Markup
from sqlalchemy import func
from wtforms.fields.choices import SelectField
from wtforms.widgets import html_params


from app.helpers.tag_colors import get_color_choices


def tag_pill_markup(text, color):
    """
    Generates an HTML `span` element with bootstrap badge classes for a pill-styled badge.
    This utility method is typically used to generate markup for styled text with a given 
    color as part of a UI or web application.
    
    :param text: The text content that will appear inside the badge.
    :type text: str
    :param color: The color of the badge, determining the visual style. Assumed to
                  be predefined so that badge-{color} forms a valid CSS class.
    :type color: str
    :return: A string containing the HTML for the pill badge element.
    :rtype: str
    """
    return f"<span class='badge badge-pill badge-{color}'>{text}</span>"


# pylint: disable=too-few-public-methods
class BootstrapSelectWidget:
    """
    Widget class for rendering a custom Bootstrap-styled <select> element.

    This class provides a styled dropdown widget compatible with Bootstrap's
    `selectpicker` component. It ensures proper integration with Bootstrap's
    styling and additional optional attributes like `data-live-search`. The
    widget allows customization and renders options with badges for a better
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
            data_content = tag_pill_markup(text=label, color=value)

            # Check if this choice is the current/selected value
            selected_html = 'selected' if field.data == value else ''

            # Render the `<option>` tag with `data-content` and selection logic
            html.append(
                f'<option value="{value}" data-content="{data_content}" {selected_html}>'
                f'{label}</option>'
            )

        html.append('</select>')
        return ''.join(html)  # Return the constructed HTML as a string


def _color_list_formatter(_view, _context, model, name):
    """
    :param _view: current administrative view
    :param _context: instance of jinja2.runtime.Context
    :param model: model instance
    :param name: property name
    :return: rendering for the column in a list view
    """
    if name == 'color' and model.color:
        return Markup(
            tag_pill_markup(text=model.color.title(), color=model.color)
        )
    return ''


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
            'choices': get_color_choices(),  # Dynamically provide choices
            'widget': BootstrapSelectWidget()  # Use the custom widget for badge-pill rendering
        }
    }
    column_formatters = {
        'color': _color_list_formatter
    }

    can_edit = True  # Allow editing lists
    can_delete = True  # Allow deleting lists
    edit_template = 'tag_edit.html'
    create_template = 'tag_create.html'

    def on_form_prefill(self, form, _id):
        if hasattr(form, 'color'):
            form.color.choices = get_color_choices()

    def validate_form(self, form):
        if hasattr(form, 'color'):
            form.color.choices = get_color_choices()
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
