__author__ = 'Yifu Huang'

from src.azureautodeploy.database.models import db

# initialize db tables
# make sure database and user correctly created in mysql
# in case upgrade the table structure, the origin table need be dropped firstly
db.create_all()