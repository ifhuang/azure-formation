__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.utility import (
    READY_ROLE,
    find_unassigned_endpoint,
    add_endpoint_to_network_config,
    delete_endpoint_from_network_config,
)
from src.azureformation.enum import (
    VIRTUAL_MACHINE,
)
from src.azureformation.log import (
    log,
)


class Endpoint:
    """
    Endpoint is used for dynamic management of azure endpoint on azure cloud service
    """
    ERROR_RESULT = -1
    TICK = 5
    LOOP = 200

    def __init__(self, service):
        self.service = service

    def assign_public_endpoint(self, cloud_service_name, deployment_slot, virtual_machine_name, private_endpoint):
        """
        Assign public endpoint of cloud service for private endpoint of virtual machine
        Return -1 if failed
        :param cloud_service_name:
        :param deployment_slot:
        :param virtual_machine_name:
        :param private_endpoint:
        :return:
        """
        assigned_endpoints = self.service.get_assigned_endpoints(cloud_service_name)
        if assigned_endpoints is None:
            return self.ERROR_RESULT
        # duplicate detection for public endpoint
        public_endpoint = find_unassigned_endpoint(int(private_endpoint), assigned_endpoints)

        deployment_name = self.service.get_deployment_name(cloud_service_name, deployment_slot)
        network_config = self.service.get_virtual_machine_network_config(cloud_service_name,
                                                                         deployment_name,
                                                                         virtual_machine_name)
        # compose new network config to update
        new_network_config = add_endpoint_to_network_config(network_config, public_endpoint, private_endpoint)
        if new_network_config is None:
            return self.ERROR_RESULT
        try:
            result = self.service.update_virtual_machine_network_config(cloud_service_name,
                                                                        deployment_name,
                                                                        virtual_machine_name,
                                                                        new_network_config)
        except Exception as e:
            log.error(e)
            return self.ERROR_RESULT
        if not self.service.wait_for_async(result.request_id, self.TICK, self.LOOP):
            log.error('wait for async fail')
            return self.ERROR_RESULT
        if not self.service.wait_for_virtual_machine(cloud_service_name,
                                                     deployment_name,
                                                     virtual_machine_name,
                                                     self.TICK,
                                                     self.LOOP,
                                                     READY_ROLE):
            log.error('%s [%s] not ready' % (VIRTUAL_MACHINE, virtual_machine_name))
            return self.ERROR_RESULT
        return public_endpoint

    def release_public_endpoint(self, cloud_service_name, deployment_slot, virtual_machine_name, private_endpoint):
        """
        Release public endpoint of cloud service according to private endpoint of virtual machine
        Return False if failed
        :param cloud_service_name:
        :param deployment_slot:
        :param virtual_machine_name:
        :param private_endpoint:
        :return:
        """
        deployment_name = self.service.get_deployment_name(cloud_service_name, deployment_slot)
        network_config = self.service.get_virtual_machine_network_config(cloud_service_name,
                                                                         deployment_name,
                                                                         virtual_machine_name)
        new_network_config = delete_endpoint_from_network_config(network_config, private_endpoint)
        if new_network_config is None:
            return False
        try:
            result = self.service.update_virtual_machine_network_config(cloud_service_name,
                                                                        deployment_name,
                                                                        virtual_machine_name,
                                                                        new_network_config)
        except Exception as e:
            log.error(e)
            return False
        if not self.service.wait_for_async(result.request_id, self.TICK, self.LOOP):
            log.error('wait for async fail')
            return False
        if not self.service.wait_for_virtual_machine(cloud_service_name,
                                                     deployment_name,
                                                     virtual_machine_name,
                                                     self.TICK,
                                                     self.LOOP,
                                                     READY_ROLE):
            log.error('%s [%s] not ready' % (VIRTUAL_MACHINE, virtual_machine_name))
            return False
        return True