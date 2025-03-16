from flask import render_template, request, jsonify

from app.categories import get_category_bs_tree, id_to_fullpath


def register_routes(app):
    """
    Register application routes to the given Flask app instance.

    This function sets up the necessary routes for the Flask application,
    allowing the app to handle HTTP requests properly. It connects specific
    URL routes to their corresponding view functions.

    :param app: The Flask application instance to register routes to.
    :type app: Flask
    :return: None
    """
    @app.route('/')
    def hello_world():  # put application's code here
        category_bs_tree = get_category_bs_tree()
        return render_template('index.html', category_bs_tree=category_bs_tree)

    @app.route('/search', methods=['GET'])
    def search():
        # Extract category parms and decode to full path strings
        categories_fullpath = [
            id_to_fullpath(category) for category in request.args.getlist('cat')
        ]

        # Example response, for testing and development
        return jsonify({
            'categories_fullpath': categories_fullpath
        })
