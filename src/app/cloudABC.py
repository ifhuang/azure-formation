__author__ = 'Yifu Huang'

from src.app.database import *
from src.app.log import *
from abc import *


class CloudABC:

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def register(self, name, email):
        user_info = UserInfo.query.filter_by(name=name, email=email).first()
        # avoid duplicate user info
        if user_info is None:
            user_info = UserInfo(name, email)
            db.session.add(user_info)
            db.session.commit()
        else:
            log.debug('user info [%d] has registered' % user_info.id)
        return user_info

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def create_vm(self):
        pass

    @abstractmethod
    def update_vm(self):
        pass

    @abstractmethod
    def delete_vm(self):
        pass