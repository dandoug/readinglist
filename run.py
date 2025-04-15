"""
This module initializes and runs a Flask application instance created using the create_app() 
factory function from the app module. The application is configured to run on host 0.0.0.0 and 
port 8000 with debugging turned off.
"""
from app import create_app

app = create_app()
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8000)
