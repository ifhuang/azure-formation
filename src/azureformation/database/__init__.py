__author__ = 'Yifu Huang'

from src.azureformation.database.db_adapters import (
    SQLAlchemyAdapter,
)
from src.azureformation.functions import (
    safe_get_config,
)
from sqlalchemy import (
    create_engine,
)
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
from sqlalchemy.ext.declarative import (
    declarative_base,
)

MYSQL_CONNECTION = 'mysql.connection'
DEFAULT_URL = 'mysql://root:root@localhost/azureformation'

engine = create_engine(safe_get_config(MYSQL_CONNECTION, DEFAULT_URL),
                       convert_unicode=True,
                       pool_size=50,
                       max_overflow=100,
                       echo=False)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()
db_adapter = SQLAlchemyAdapter(db_session)