__author__ = 'Yifu Huang'

from src.app.azureImpl import AzureImpl
from src.app.database import *
from src.app.database.models import *
import sys

if __name__ == "__main__":
    print hex(id(db))
    args = sys.argv[1:]
    a = AzureImpl()
    user_info = db_adapter.get_object(UserInfo, args[0])
    a.connect(user_info)
    user_template = db_adapter.get_object(UserTemplate, args[1])
    r = a.create_sync(user_template)
    if r is False:
        sys.exit(-1)