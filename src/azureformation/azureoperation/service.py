__author__ = 'Yifu Huang'

from src.azureformation.enum import (
    ADStatus,
)
from src.azureformation.log import (
    log,
)
from azure.servicemanagement import (
    ServiceManagementService,
)
import time


class Service(ServiceManagementService):
    """
    Wrapper of azure service management service
    """
    IN_PROGRESS = 'InProgress'
    SUCCEEDED = 'Succeeded'
    NOT_FOUND = 'Not found (Not Found)'
    NETWORK_CONFIGURATION = 'NetworkConfiguration'

    def __init__(self, subscription_id, pem_url, management_host):
        super(Service, self).__init__(subscription_id, pem_url, management_host)

    # ---------------------------------------- subscription ---------------------------------------- #

    def get_subscription(self):
        return super(Service, self).get_subscription()

    # ---------------------------------------- storage account ---------------------------------------- #

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
            if e.message != self.NOT_FOUND:
                log.error(e)
            return False
        return props is not None

    def check_storage_account_name_availability(self, name):
        return super(Service, self).check_storage_account_name_availability(name)

    def create_storage_account(self, name, description, label, location):
        return super(Service, self).create_storage_account(name, description, label, location=location)

    # ---------------------------------------- cloud service ---------------------------------------- #

    def get_hosted_service_properties(self, name, detail=False):
        return super(Service, self).get_hosted_service_properties(name, detail)

    def cloud_service_exists(self, name):
        """
        Check whether specific cloud service exist in specific azure subscription
        :param name:
        :return:
        """
        try:
            props = self.get_hosted_service_properties(name)
        except Exception as e:
            if e.message != self.NOT_FOUND:
                log.error(e)
            return False
        return props is not None

    def check_hosted_service_name_availability(self, name):
        return super(Service, self).check_hosted_service_name_availability(name)

    def create_hosted_service(self, name, label, location):
        return super(Service, self).create_hosted_service(name, label, location=location)

    # ---------------------------------------- deployment ---------------------------------------- #

    def get_deployment_by_slot(self, cloud_service_name, deployment_slot):
        return super(Service, self).get_deployment_by_slot(cloud_service_name, deployment_slot)

    def get_deployment_by_name(self, cloud_service_name, deployment_name):
        return super(Service, self).get_deployment_by_name(cloud_service_name, deployment_name)

    def deployment_exists(self, cloud_service_name, deployment_slot):
        try:
            props = self.get_deployment_by_slot(cloud_service_name, deployment_slot)
        except Exception as e:
            if e.message != self.NOT_FOUND:
                log.error(e)
            return False
        return props is not None

    def get_deployment_name(self, cloud_service_name, deployment_slot):
        try:
            props = self.get_deployment_by_slot(cloud_service_name, deployment_slot)
        except Exception as e:
            log.error(e)
            return None
        return None if props is None else props.name

    def wait_for_deployment(self, cloud_service_name, deployment_name, second_per_loop, loop, status=ADStatus.RUNNING):
        count = 0
        props = self.get_deployment_by_name(cloud_service_name, deployment_name)
        while props.status != status:
            log.debug('wait for deployment [%s] loop count: %d' % (deployment_name, count))
            count += 1
            if count > loop:
                log.error('Timed out waiting for deployment status.')
                return False
            time.sleep(second_per_loop)
            props = self.get_deployment_by_name(cloud_service_name, deployment_name)
        return props.status == status

    def get_deployment_dns(self, cloud_service_name, deployment_slot):
        try:
            props = self.get_deployment_by_slot(cloud_service_name, deployment_slot)
        except Exception as e:
            log.error(e)
            return None
        return None if props is None else props.url

    # ---------------------------------------- virtual machine ---------------------------------------- #

    def create_virtual_machine_deployment(self,
                                          cloud_service_name,
                                          deployment_name,
                                          deployment_slot,
                                          virtual_machine_label,
                                          virtual_machine_name,
                                          system_config,
                                          os_virtual_hard_disk,
                                          network_config,
                                          virtual_machine_size,
                                          vm_image_name):
        return super(Service, self).create_virtual_machine_deployment(cloud_service_name,
                                                                      deployment_name,
                                                                      deployment_slot,
                                                                      virtual_machine_label,
                                                                      virtual_machine_name,
                                                                      system_config,
                                                                      os_virtual_hard_disk,
                                                                      network_config=network_config,
                                                                      role_size=virtual_machine_size,
                                                                      vm_image_name=vm_image_name)

    def get_virtual_machine_instance_status(self, deployment, virtual_machine_name):
        for role_instance in deployment.role_instance_list:
            if role_instance.instance_name == virtual_machine_name:
                return role_instance.instance_status
        return None

    def wait_for_virtual_machine(self,
                                 cloud_service_name,
                                 deployment_name,
                                 virtual_machine_name,
                                 second_per_loop,
                                 loop,
                                 status):
        count = 0
        props = self.get_deployment_by_name(cloud_service_name, deployment_name)
        while self.get_virtual_machine_instance_status(props, virtual_machine_name) != status:
            log.debug('wait for virtual machine [%s] loop count: %d' % (virtual_machine_name, count))
            count += 1
            if count > loop:
                log.error('Timed out waiting for role instance status.')
                return False
            time.sleep(second_per_loop)
            props = self.get_deployment_by_name(cloud_service_name, deployment_name)
        return self.get_virtual_machine_instance_status(props, virtual_machine_name) == status

    def update_virtual_machine_network_config(self,
                                              cloud_service_name,
                                              deployment_name,
                                              virtual_machine_name,
                                              network_config):
        return super(Service, self).update_role(cloud_service_name,
                                                deployment_name,
                                                virtual_machine_name,
                                                network_config=network_config)

    def get_virtual_machine_public_ip(self, cloud_service_name, deployment_name, virtual_machine_name):
        deployment = self.get_deployment_by_name(cloud_service_name, deployment_name)
        for role in deployment.role_instance_list:
            if role.role_name == virtual_machine_name:
                if role.instance_endpoints is not None:
                    return role.instance_endpoints.instance_endpoints[0].vip
        return None

    def get_virtual_machine_private_ip(self, cloud_service_name, deployment_name, virtual_machine_name):
        deployment = self.get_deployment_by_name(cloud_service_name, deployment_name)
        for role in deployment.role_instance_list:
            if role.role_name == virtual_machine_name:
                return role.ip_address
        return None

    def get_virtual_machine(self, cloud_service_name, deployment_name, role_name):
        return super(Service, self).get_role(cloud_service_name, deployment_name, role_name)

    def virtual_machine_exists(self, cloud_service_name, deployment_name, virtual_machine_name):
        try:
            props = self.get_virtual_machine(cloud_service_name, deployment_name, virtual_machine_name)
        except Exception as e:
            if e.message != self.NOT_FOUND:
                log.error(e)
            return False
        return props is not None

    def add_virtual_machine(self,
                            cloud_service_name,
                            deployment_name,
                            virtual_machine_name,
                            system_config,
                            os_virtual_hard_disk,
                            network_config,
                            virtual_machine_size,
                            vm_image_name):
        return super(Service, self).add_role(cloud_service_name,
                                             deployment_name,
                                             virtual_machine_name,
                                             system_config,
                                             os_virtual_hard_disk,
                                             network_config=network_config,
                                             role_size=virtual_machine_size,
                                             vm_image_name=vm_image_name)

    # ---------------------------------------- endpoint ---------------------------------------- #

    def get_assigned_endpoints(self, cloud_service_name):
        properties = self.get_hosted_service_properties(cloud_service_name, True)
        endpoints = []
        for deployment in properties.deployments.deployments:
            for role in deployment.role_list.roles:
                for configuration_set in role.configuration_sets.configuration_sets:
                    if configuration_set.configuration_set_type == self.NETWORK_CONFIGURATION:
                        if configuration_set.input_endpoints is not None:
                            for input_endpoint in configuration_set.input_endpoints.input_endpoints:
                                endpoints.append(input_endpoint.port)
        return endpoints

    def get_public_endpoint(self, cloud_service_name, endpoint_name):
        properties = self.get_hosted_service_properties(cloud_service_name, True)
        for deployment in properties.deployments.deployments:
            for role in deployment.role_list.roles:
                for configuration_set in role.configuration_sets.configuration_sets:
                    if configuration_set.configuration_set_type == self.NETWORK_CONFIGURATION:
                        if configuration_set.input_endpoints is not None:
                            for input_endpoint in configuration_set.input_endpoints.input_endpoints:
                                if input_endpoint.name == endpoint_name:
                                    return input_endpoint.port
        return None

    # ---------------------------------------- other ---------------------------------------- #

    def get_operation_status(self, request_id):
        return super(Service, self).get_operation_status(request_id)

    def wait_for_async(self, request_id, second_per_loop, loop):
        """
        Wait for async operation, up to second_per_loop * loop
        :param request_id:
        :return:
        """
        count = 0
        result = self.get_operation_status(request_id)
        while result.status == self.IN_PROGRESS:
            log.debug('wait for async [%s] loop count [%d]' % (request_id, count))
            count += 1
            if count > loop:
                log.error('Timed out waiting for async operation to complete.')
                return False
            time.sleep(second_per_loop)
            result = self.get_operation_status(request_id)
        if result.status != self.SUCCEEDED:
            log.error(vars(result))
            if result.error:
                log.error(result.error.code)
                log.error(vars(result.error))
            log.error('Asynchronous operation did not succeed.')
            return False
        return True