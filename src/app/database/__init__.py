__author__ = 'Yifu Huang'

from src.app import app
from src.app.database.db_adapters import SQLAlchemyAdapter
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)
db_adapter = SQLAlchemyAdapter(db)