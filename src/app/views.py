__author__ = 'Yifu Huang'

from app import app

@app.route('/')
def index():
    return 'Hello World!'