__author__ = 'Yifu Huang'

from src.azureformation.log import (
    log
)


class Subscription:
    """
    Subscription of azure resources according to given subscription id
    """

    def __init__(self, service):
        self.service = service

    def get_available_storage_account_count(self):
        """
        Get available count of storage account
        Return -1 if failed
        :return:
        """
        try:
            result = self.service.get_subscription()
        except Exception as e:
            log.error(e)
            return -1
        return result.max_storage_accounts - result.current_storage_accounts

    def get_available_cloud_service_count(self):
        """
        Get available count of cloud service
        Return -1 if failed
        :return:
        """
        try:
            result = self.service.get_subscription()
        except Exception as e:
            log.error(e)
            return -1
        return result.max_hosted_services - result.current_hosted_services

    def get_available_core_count(self):
        """
        Get available count of core
        Return -1 if failed
        :return:
        """
        try:
            result = self.service.get_subscription()
        except Exception as e:
            log.error(e)
            return -1
        return result.max_core_count - result.current_core_count