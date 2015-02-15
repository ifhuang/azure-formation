__author__ = 'Yifu Huang'


from azure.servicemanagement import ServiceManagementService


class Service(ServiceManagementService):
    """
    Wrapper of azure service management service
    """

    def __init__(self, subscription_id, pem_url, management_host):
        super(Service, self).__init__(subscription_id, pem_url, management_host)
