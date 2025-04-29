"""
This module provides functionality to interact with the ASIN Data API for 
retrieving detailed product information based on an ASIN (Amazon Standard 
Identification Number). The `fetch_product_details` function sends a request 
to the API and processes the response to extract meaningful product attributes, 
such as title, authors, categories, ratings, and ISBN. The module is
designed to be integrated with a Flask application and requires a valid API key 
to function.
"""
import requests
from flask import current_app

from app.helpers.utilities import sanitize, sanitize_categories_flat


# Fetch the product details from the ASIN Data API
def fetch_product_details(asin):
    """
    Fetches detailed product information using the ASIN Data API.

    This function retrieves product details for a given ASIN (Amazon Standard
    Identification Number) by performing a GET request to the ASIN Data
    API. It processes the API response and extracts specific data attributes
    related to the product, such as the title, rating, authors, description,
    ISBNs, etc. The result is returned as a structured dictionary.

    :param asin: A string representing the ASIN (Amazon Standard
        Identification Number) of the desired product to fetch details for.
    :return: A dictionary containing structured product details fetched
        from the API, including attributes such as title, author, image,
        ISBNs, categories, and more. Returns an empty dictionary
        if the product details are unavailable.
    :raises ValueError: If the API key for ASIN Data API is missing
        in the application configuration.
    :raises HTTPError: If the HTTP request to the ASIN Data API fails or
        returns a response with a status code indicating an error.
    """
    # Retrieve the api_key from app.config
    api_key = current_app.config.get('ASIN_DATA_API_KEY')
    if not api_key:
        raise ValueError('ASIN Data API key is missing from configuration!')

    # See https://trajectdata.com/ecommerce/asin-data-api/
    api_url = current_app.config.get('ASIN_DATA_API_URL', 'https://api.asindataapi.com/request')

    # set up the request parameters
    params = {
        'api_key': api_key,
        'amazon_domain': 'amazon.com',
        'asin': asin,
        'type': 'product',
        'output': 'json'
    }
    # make the http GET request to ASIN Data API
    response = requests.get(api_url, params, timeout=30)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

    catalog_data = response.json()
    if catalog_data.get('product'):
        product = catalog_data.get('product')
        if product:
            # these attributes are simple pass-throughs
            attributes = [
                'title',
                'asin',
                'book_description',
                'rating',
                'link',
                'bestsellers_rank_flat',
                'specifications_flat'
            ]
            return_value = {}
            for attribute in attributes:
                if product.get(attribute):
                    return_value[attribute] = sanitize(product[attribute])
            # Special processing attributes
            if product.get('authors'):
                return_value['author'] = sanitize(product['authors'][0]['name'])
            if product.get('categories'):
                cat_list = [c['name'] for c in product['categories'] if 'name' in c]
                return_value['categories_flat'] = sanitize_categories_flat(' > '.join(cat_list))
            if product.get('main_image'):
                return_value['image'] = product['main_image']['link']
            if product.get('specifications'):
                specs = product['specifications']
                hardcover_str = next((s['value'] for s in specs if s['name'] == 'Hardcover'), None)
                if hardcover_str:
                    return_value['hardcover'] = sanitize(hardcover_str)
                isbn_10_str = next((s['value'] for s in specs if s['name'] == 'ISBN-10'), None)
                if isbn_10_str:
                    return_value['isbn_10'] = sanitize(isbn_10_str)
                isbn_13_str = next((s['value'] for s in specs if s['name'] == 'ISBN-13'), None)
                if isbn_13_str:
                    return_value['isbn_13'] = sanitize(isbn_13_str)

            return return_value
    return {}  # empty if errors
