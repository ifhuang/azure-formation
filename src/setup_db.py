from src.azureformation.database import (
    engine,
)
from src.azureformation.database.models import (
    Base,
)


def setup_db():
    # initialize db tables
    # make sure database and user correctly created in mysql
    # in case upgrade the table structure, the origin table need be dropped firstly
    Base.metadata.create_all(bind=engine)

setup_db()