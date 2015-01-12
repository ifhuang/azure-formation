__author__ = 'Yifu Huang'

from abc import *
from database import *


class CloudABC:

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def register(self, name, email):
        user_info = UserInfo(name, email)
        db.session.add(user_info)
        db.session.commit()
        return user_info

    @abstractmethod
    def connect(self):
        pass