import pytest
from flask import Flask
from app.services import fetch_product_details


def test_fetch_product_details_no_api_key(mocker):
    # Create a Flask app instance
    app = Flask(__name__)

    # Within the application's context
    with app.app_context():
        # Mock `current_app.config` so that 'ASIN_DATA_API_KEY' returns `None`
        mocker.patch.dict(app.config, {"ASIN_DATA_API_KEY": None})

        # Provide a sample ASIN for the test
        sample_asin = "B08K9347FG"

        # Test the behavior of fetch_product_details
        with pytest.raises(ValueError, match="ASIN Data API key is missing from configuration!"):
            fetch_product_details(sample_asin)
