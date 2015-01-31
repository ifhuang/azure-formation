__author__ = 'Yifu Huang'

from src.azureautodeploy import app
from src.azureautodeploy.database.db_adapters import SQLAlchemyAdapter
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)
db_adapter = SQLAlchemyAdapter(db)