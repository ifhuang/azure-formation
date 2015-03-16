from src.azureformation.database import (
    engine,
)
from src.azureformation.database.models import (
    Base,
)
from src.setup_db import (
    setup_db,
)

Base.metadata.drop_all(bind=engine)
setup_db()
