__author__ = 'Yifu Huang'

from src.azureautodeploy.database import *
from src.azureautodeploy.database.models import *
import time


def test():
    db_adapter.add_object_kwargs(UserOperation, user_template=None, operation='create', status='start')
    db_adapter.commit()

if __name__ == "__main__":
    print hex(id(db))
    while True:
        test()
        time.sleep(2)