__author__ = 'Yifu Huang'

from src.azureautodeploy.functions import *
from flask import Flask

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = safe_get_config("mysql/connection",
                                                        "mysql://root:root@localhost/azureautodeploy")

from src.azureautodeploy import views