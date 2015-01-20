__author__ = 'Yifu Huang'

from src.app.database import *
from src.app.log import *
from abc import *


class CloudABC:
    """
    Abstract base class for cloud service management
    Any specific cloud service management should inherit from this class
    Currently support only Azure
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def register(self, name, email):
        """
        Create user info according to give name and email
        :param name:
        :param email:
        :return: user info
        """
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
    def connect(self, user_info):
        """
        Connect to cloud according to given user_info
        :param user_info:
        :return:
        """
        pass

    @abstractmethod
    def create(self, user_template):
        """
        Create virtual machines according to give user template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def update(self, user_template):
        """
        Update virtual machines according to given user template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def delete(self, user_template):
        """
        Delete virtual machines according to given user template
        :param user_template:
        :return:
        """
        pass
