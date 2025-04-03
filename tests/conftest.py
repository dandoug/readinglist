import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set the environment variable FLASK_ENV to "testing"
os.environ["FLASK_ENV"] = "testing"
