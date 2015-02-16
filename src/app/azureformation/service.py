__author__ = 'Yifu Huang'


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

    def get_storage_account_properties(self, service_name):
        return super(Service, self).get_storage_account_properties(service_name)

    def check_storage_account_name_availability(self, service_name):
        return super(Service, self).check_storage_account_name_availability(service_name)

    def create_storage_account(self, service_name, description, label, location):
        return super(Service, self).create_storage_account(service_name, description, label, location=location)

    # ---------------------------------------- other ---------------------------------------- #

    def get_operation_status(self, request_id):
        return super(Service, self).get_operation_status(request_id)