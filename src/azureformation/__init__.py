__author__ = 'Yifu Huang'

from src.azureformation.functions import (
    safe_get_config,
)
from flask import (
    Flask,
)

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = safe_get_config("mysql/connection",
                                                        "mysql://root:root@localhost/azureformation")

from src.azureformation import (
    views,
)