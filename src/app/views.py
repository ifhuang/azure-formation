__author__ = 'Yifu Huang'

from src.app import app


@app.route('/')
def index():
    return 'Hello World!'