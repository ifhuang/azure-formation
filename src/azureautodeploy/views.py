__author__ = 'Yifu Huang'

from src.azureautodeploy import app


@app.route('/')
def index():
    return 'Hello World!'