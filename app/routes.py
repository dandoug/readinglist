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
        """
        Handle the /search route, extracting 'cat' query parameters.

        :return: JSON response with the list of 'cat' parameter values.
        """
        # Use `getlist` to capture 'cat' parameters (one, none, or many)
        categories = request.args.getlist('cat')

        # Convert category IDs to their full path representation
        categories_fullpath = [id_to_fullpath(category) for category in categories]

        # Example response, for testing and development
        return jsonify({
            'categories': categories,
            'categories_fullpath': categories_fullpath,
            'message': 'Search successful!',
        })
