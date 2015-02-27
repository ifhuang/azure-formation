__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.subscription import (
    Subscription
)
from src.azureformation.azureoperation.utility import (
    ASYNC_TICK,
    ASYNC_LOOP,
    DEPLOYMENT_TICK,
    DEPLOYMENT_LOOP,
    VIRTUAL_MACHINE_TICK,
    VIRTUAL_MACHINE_LOOP,
    AZURE_FORMATION,
    commit_azure_log,
    delete_azure_deployment,
    commit_azure_deployment,
    commit_azure_virtual_machine,
    commit_virtual_environment,
    contain_azure_deployment,
    contain_azure_virtual_machine,
    delete_azure_virtual_machine
)
from src.azureformation.enum import (
    ALOperation,
    ALStatus,
    DEPLOYMENT,
    VIRTUAL_MACHINE,
    ADStatus,
    AVMStatus,
    VEProvider,
    VERemoteProvider,
    VEStatus
)
from src.azureformation.log import (
    log
)

create_deployment_error = [
    '%s [%s] %s',
    '%s [%s] wait for async fail',
    '%s [%s] wait for deployment fail',
    '%s [%s] subscription not enough'
]
create_deployment_info = [
    '%s [%s] created',
    '%s [%s] exist but not created by %s before',
    '%s [%s] exist and created by %s before'
]
create_virtual_machine_error = [
    '%s [%s] %s',
    '%s [%s] wait for async fail',
    '%s [%s] wait for virtual machine fail',
    '%s [%s] wait for async fail (update network config)',
    '%s [%s] wait for virtual machine fail (update network config)',
    '%s [%s] exist but not created by %s before',
    '%s [%s] subscription not enough'
]
create_virtual_machine_info = [
    '%s [%s] created',
    '%s [%s] exist and created by %s before'
]
size_core_map = {
    'a0': 1,
    'basic_a0': 1,
    'a1': 1,
    'basic_a1': 1,
    'a2': 2,
    'basic_a2': 2,
    'a3': 4,
    'basic_a3': 4,
    'a4': 8,
    'basic_a4': 8,
    'extra small': 1,
    'small': 1,
    'medium': 2,
    'large': 4,
    'extra large': 8,
    'a5': 2,
    'a6': 4,
    'a7': 8,
    'a8': 8,
    'a9': 16,
    'standard_d1': 1,
    'standard_d2': 2,
    'standard_d3': 4,
    'standard_d4': 8,
    'standard_d11': 2,
    'standard_d12': 4,
    'standard_d13': 8,
    'standard_d14': 16,
    'standard_ds1': 1,
    'standard_ds2': 2,
    'standard_ds3': 4,
    'standard_ds4': 8,
    'standard_ds11': 2,
    'standard_ds12': 4,
    'standard_ds13': 8,
    'standard_ds14': 16,
    'standard_g1': 2,
    'standard_g2': 4,
    'standard_g3': 8,
    'standard_g4': 16,
    'standard_g5': 32
}


class VirtualMachine:
    """
    Virtual machine is azure virtual machine with its azure deployment
    """

    def __init__(self, service):
        self.service = service
        self.subscription = Subscription(service)

    def create_virtual_machine(self, template, experiment):
        """
        1. If deployment not exist in azure subscription, then create virtual machine with deployment
           Else reuse deployment in azure subscription
        2. If virtual machine not exist in azure subscription, then add virtual machine to deployment
           Else reuse virtual machine in azure subscription
        :return:
        """
        commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.START)
        commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.START)
        cloud_service_name = template.get_cloud_service_name()
        deployment_slot = template.get_deployment_slot()
        virtual_machine_name = '%s-%d' % (template.get_virtual_machine_name(), experiment.id)
        virtual_machine_size = template.get_virtual_machine_size()
        if self.subscription.get_available_core_count() < size_core_map[virtual_machine_size.lower()]:
            m = create_deployment_error[3] % (DEPLOYMENT, deployment_slot)
            commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.FAIL, m, 3)
            log.error(m)
            m = create_virtual_machine_error[6] % (VIRTUAL_MACHINE, virtual_machine_name)
            commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 6)
            log.error(m)
            return False
        virtual_machine_label = template.get_virtual_machine_label()
        system_config = template.get_system_config()
        os_virtual_hard_disk = template.get_os_virtual_hard_disk()
        network_config = template.get_network_config()
        image_type = template.get_image_type()
        image_name = template.get_image_name()
        # avoid duplicate deployment in azure subscription
        if self.service.deployment_exists(cloud_service_name, deployment_slot):
            deployment_name = self.service.get_deployment_name(cloud_service_name, deployment_slot)
            if contain_azure_deployment(cloud_service_name, deployment_slot):
                m = create_deployment_info[0] % (DEPLOYMENT, deployment_name, AZURE_FORMATION)
                commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.END, m, 2)
            else:
                m = create_deployment_info[1] % (DEPLOYMENT, deployment_name, AZURE_FORMATION)
                commit_azure_deployment(deployment_name,
                                        deployment_slot,
                                        ADStatus.RUNNING,
                                        cloud_service_name,
                                        experiment)
                commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.END, m, 1)
            log.debug(m)
            # avoid duplicate role in azure subscription
            if self.service.role_exists(cloud_service_name, deployment_name, virtual_machine_name):
                if contain_azure_virtual_machine(cloud_service_name, deployment_name, virtual_machine_name):
                    m = create_virtual_machine_info[1] % (VIRTUAL_MACHINE, virtual_machine_name, AZURE_FORMATION)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.END, m, 1)
                    log.debug(m)
                else:
                    m = create_virtual_machine_error[5] % (VIRTUAL_MACHINE, virtual_machine_name, AZURE_FORMATION)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 5)
                    log.error(m)
                    return False
            else:
                # delete old azure virtual machine, cascade delete old azure endpoint
                delete_azure_virtual_machine(cloud_service_name, deployment_name, virtual_machine_name)
                try:
                    result = self.service.add_role(cloud_service_name,
                                                   deployment_name,
                                                   virtual_machine_name,
                                                   system_config,
                                                   os_virtual_hard_disk,
                                                   network_config,
                                                   image_name,
                                                   virtual_machine_size)
                except Exception as e:
                    m = create_virtual_machine_error[0] % (VIRTUAL_MACHINE, virtual_machine_name, e.message)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, e.message, 0)
                    log.error(e)
                    return False
                # make sure async operation succeeds
                if not self.service.wait_for_async(result.request_id, ASYNC_TICK, ASYNC_LOOP):
                    m = create_virtual_machine_error[1] % (VIRTUAL_MACHINE, virtual_machine_name)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 1)
                    log.error(m)
                    return False
                # make sure role is ready
                if not self.service.wait_for_role(cloud_service_name,
                                                  deployment_name,
                                                  virtual_machine_name,
                                                  VIRTUAL_MACHINE_TICK,
                                                  VIRTUAL_MACHINE_LOOP):
                    m = create_virtual_machine_error[2] % (VIRTUAL_MACHINE, virtual_machine_name)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 2)
                    log.error(m)
                    return False
                else:
                    dns = self.service.get_deployment_dns(cloud_service_name, deployment_slot)
                    public_ip = self.service.get_virtual_machine_public_ip(cloud_service_name,
                                                                           deployment_name,
                                                                           virtual_machine_name)
                    private_ip = self.service.get_virtual_machine_private_ip(cloud_service_name,
                                                                             deployment_name,
                                                                             virtual_machine_name)
                    commit_azure_virtual_machine(virtual_machine_name,
                                                 virtual_machine_label,
                                                 AVMStatus.RUNNING,
                                                 dns,
                                                 public_ip,
                                                 private_ip,
                                                 cloud_service_name,
                                                 deployment_name,
                                                 experiment)
                    remote_port_name = template.get_remote_port_name()
                    remote_port = self.service.get_public_endpoint(remote_port_name)
                    remote_paras = template.get_remote_paras(virtual_machine_name,
                                                             public_ip,
                                                             remote_port)
                    commit_virtual_environment(VEProvider.AzureVM,
                                               template.get_remote_provider_name(),
                                               None,
                                               VEStatus.Running,
                                               VERemoteProvider.Guacamole,
                                               remote_paras,
                                               experiment)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.END)
        else:
            # delete old azure deployment, cascade delete old azure virtual machine and azure endpoint
            delete_azure_deployment(cloud_service_name, deployment_slot)
            deployment_name = template.get_deployment_name()
            try:
                result = self.service.create_virtual_machine_deployment(cloud_service_name,
                                                                        deployment_name,
                                                                        deployment_slot,
                                                                        virtual_machine_label,
                                                                        virtual_machine_name,
                                                                        system_config,
                                                                        os_virtual_hard_disk,
                                                                        network_config,
                                                                        role_size=virtual_machine_size)
            except Exception as e:
                m = create_deployment_error[0] % (DEPLOYMENT, deployment_slot, e.message)
                commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.FAIL, m, 0)
                m = create_virtual_machine_error[0] % (VIRTUAL_MACHINE, virtual_machine_name, e.message)
                commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 0)
                log.error(e)
                return False
            # make sure async operation succeeds
            if not self.service.wait_for_async(result.request_id, ASYNC_TICK, ASYNC_LOOP):
                m = create_deployment_error[1] % (DEPLOYMENT, deployment_slot)
                commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.FAIL, m, 1)
                log.error(m)
                m = create_virtual_machine_error[1] % (VIRTUAL_MACHINE, virtual_machine_name)
                commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 1)
                log.error(m)
                return False
            # make sure deployment is ready
            if not self.service.wait_for_deployment(cloud_service_name,
                                                    deployment_name,
                                                    DEPLOYMENT_TICK,
                                                    DEPLOYMENT_LOOP):
                m = create_deployment_error[2] % (DEPLOYMENT, deployment_slot)
                commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.FAIL, m, 2)
                log.error(m)
                return False
            else:
                commit_azure_deployment(deployment_name,
                                        deployment_slot,
                                        ADStatus.RUNNING,
                                        cloud_service_name,
                                        experiment)
                commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.END)
            # make sure role is ready
            if not self.service.wait_for_virtual_machine(cloud_service_name,
                                                         deployment_name,
                                                         virtual_machine_name,
                                                         VIRTUAL_MACHINE_TICK,
                                                         VIRTUAL_MACHINE_LOOP):
                m = create_virtual_machine_error[2] % (VIRTUAL_MACHINE, virtual_machine_name)
                commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 2)
                log.error(m)
                return False
            else:
                result = self.service.update_role(cloud_service_name,
                                                  deployment_name,
                                                  virtual_machine_name,
                                                  network_config)
                if not self.service.wait_for_async(result.request_id, ASYNC_TICK, ASYNC_LOOP):
                    m = create_virtual_machine_error[3] % (VIRTUAL_MACHINE, virtual_machine_name)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 3)
                    log.error(m)
                    return False
                if not self.service.wait_for_virtual_machine(cloud_service_name,
                                                             deployment_name,
                                                             virtual_machine_name,
                                                             VIRTUAL_MACHINE_TICK,
                                                             VIRTUAL_MACHINE_LOOP):
                    m = create_virtual_machine_error[4] % (VIRTUAL_MACHINE, virtual_machine_name)
                    commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 4)
                    log.error(m)
                    return False
                dns = self.service.get_deployment_dns(cloud_service_name, deployment_slot)
                public_ip = self.service.get_virtual_machine_public_ip(cloud_service_name,
                                                                       deployment_name,
                                                                       virtual_machine_name)
                private_ip = self.service.get_virtual_machine_private_ip(cloud_service_name,
                                                                         deployment_name,
                                                                         virtual_machine_name)
                commit_azure_virtual_machine(virtual_machine_name,
                                             virtual_machine_label,
                                             AVMStatus.RUNNING,
                                             dns,
                                             public_ip,
                                             private_ip,
                                             cloud_service_name,
                                             deployment_name,
                                             experiment)
                remote_port_name = template.get_remote_port_name()
                remote_port = self.service.get_public_endpoint(remote_port_name)
                remote_paras = template.get_remote_paras(virtual_machine_name,
                                                         public_ip,
                                                         remote_port)
                commit_virtual_environment(VEProvider.AzureVM,
                                           template.get_remote_provider_name(),
                                           None,
                                           VEStatus.Running,
                                           VERemoteProvider.Guacamole,
                                           remote_paras,
                                           experiment)
                commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.END)
        return True

    # todo shutdown virtual machine
    def shutdown_virtual_machine(self):
        raise NotImplementedError

    # todo start virtual machine
    def start_virtual_machine(self):
        raise NotImplementedError

    # todo delete virtual machine
    def delete_virtual_machine(self):
        raise NotImplementedError