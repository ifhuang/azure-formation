__author__ = 'Yifu Huang'


from src.app.azureformation.utility import NOT_FOUND
from src.app.log import log
from azure.servicemanagement import ServiceManagementService


class Service(ServiceManagementService):
    """
    Wrapper of azure service management service
    """

    def __init__(self, subscription_id, pem_url, management_host):
        super(Service, self).__init__(subscription_id, pem_url, management_host)

    # ---------------------------------------- subscription ---------------------------------------- #

    def get_subscription(self):
        return super(Service, self).get_subscription()

    # ---------------------------------------- storage ---------------------------------------- #

    def get_storage_account_properties(self, name):
        return super(Service, self).get_storage_account_properties(name)

    def storage_account_exists(self, name):
        """
        Check whether specific storage account exist in specific azure subscription
        :param name:
        :return:
        """
        try:
            props = self.get_storage_account_properties(name)
        except Exception as e:
            if e.message != NOT_FOUND:
                log.error(e)
            return False
        return props is not None

    def check_storage_account_name_availability(self, name):
        return super(Service, self).check_storage_account_name_availability(name)

    def create_storage_account(self, name, description, label, location):
        return super(Service, self).create_storage_account(name, description, label, location=location)

    # ---------------------------------------- cloud service ---------------------------------------- #

    def get_hosted_service_properties(self, name):
        return super(Service, self).get_hosted_service_properties(name)

    def cloud_service_exists(self, name):
        """
        Check whether specific cloud service exist in specific azure subscription
        :param name:
        :return:
        """
        try:
            props = self.get_hosted_service_properties(name)
        except Exception as e:
            if e.message != NOT_FOUND:
                log.error(e)
            return False
        return props is not None

    def check_hosted_service_name_availability(self, name):
        return super(Service, self).check_hosted_service_name_availability(name)

    def create_hosted_service(self, name, label, location):
        return super(Service, self).create_hosted_service(name, label, location=location)

    # ---------------------------------------- other ---------------------------------------- #

    def get_operation_status(self, request_id):
        return super(Service, self).get_operation_status(request_id)