__author__ = 'Yifu Huang'

from src.azureformation import (
    app
)


@app.route('/')
def index():
    return 'Hello World!'