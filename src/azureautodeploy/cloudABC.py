__author__ = 'Yifu Huang'

from src.azureautodeploy.database import *
from src.azureautodeploy.database.models import *
from src.azureautodeploy.log import *
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
        user_info = db_adapter.find_first_object(UserInfo, name=name, email=email)
        # avoid duplicate user info
        if user_info is None:
            user_info = db_adapter.add_object_kwargs(UserInfo, name=name, email=email)
            db_adapter.commit()
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
    def create_async(self, user_template):
        """
        Create virtual machines according to give user template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def update_async(self, user_template, update_template):
        """
        Update virtual machines created by user template according to given update template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def delete_async(self, user_template):
        """
        Delete virtual machines according to given user template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def shutdown_async(self, user_template):
        """
        Shutdown virtual machines according to given user template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def create_sync(self, user_template):
        """
        Create virtual machines according to give user template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def update_sync(self, user_template, update_template):
        """
        Update virtual machines created by user template according to given update template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def delete_sync(self, user_template):
        """
        Delete virtual machines according to given user template
        :param user_template:
        :return:
        """
        pass

    @abstractmethod
    def shutdown_sync(self, user_template):
        """
        Shutdown virtual machines according to given user template
        :param user_template:
        :return:
        """
        pass