__author__ = 'Yifu Huang'

from src.azureformation import app
from src.azureformation.database.db_adapters import SQLAlchemyAdapter
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)
db_adapter = SQLAlchemyAdapter(db)