from flask import Flask
from dotenv import load_dotenv
import os


load_dotenv()  # Loads variables from .env into the environment

app = Flask(__name__)
RDS_PORT = os.getenv('RDS_PORT')

@app.route('/')
def hello_world():  # put application's code here
    return f"Hello World!  {RDS_PORT}"


if __name__ == '__main__':
    app.run()
