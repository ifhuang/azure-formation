__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.subscription import (
    Subscription
)
from src.azureformation.azureoperation.utility import (
    ASYNC_TICK,
    ASYNC_LOOP,
    DEPLOYMENT_TICK,
    DEPLOYMENT_LOOP,
    commit_azure_log,
    delete_azure_deployment,
    commit_azure_deployment
)
from src.azureformation.enum import (
    ALOperation,
    ALStatus,
    DEPLOYMENT,
    VIRTUAL_MACHINE,
    ADStatus,
    AVMStatus
)
from src.azureformation.log import (
    log
)

create_deployment_error = [
    '%s [%s] %s',
    '%s [%s] wait for async fail',
    '%s [%s] wait for deployment fail'
]
create_deployment_info = [

]
create_virtual_machine_error = [
    '%s [%s] %s',
    '%s [%s] wait for async fail'
]
create_virtual_machine_info = [

]


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
        virtual_machine_name = template.get_virtual_machine_name()
        virtual_machine_label = template.get_virtual_machine_label()
        virtual_machine_size = template.get_virtual_machine_size()
        system_config = template.get_system_config()
        os_virtual_hard_disk = template.get_os_virtual_hard_disk()
        network_config = template.get_network_config()
        # avoid duplicate deployment in azure subscription
        if self.service.deployment_exists(cloud_service_name, deployment_slot):
            if db_adapter.count(UserResource,
                                type=DEPLOYMENT,
                                name=deployment['deployment_name'],
                                cloud_service_id=cs.id) == 0:
                m = '%s %s exist but not created by this function before' % \
                    (DEPLOYMENT, deployment['deployment_name'])
                user_resource_commit(self.user_template, DEPLOYMENT, deployment['deployment_name'], RUNNING, cs.id)
            else:
                m = '%s %s exist and created by this function before' % \
                    (DEPLOYMENT, deployment['deployment_name'])
            user_operation_commit(self.user_template, CREATE_DEPLOYMENT, END, m)
            log.debug(m)
            # avoid duplicate role
            if self.service.role_exists(cloud_service['service_name'],
                                        deployment['deployment_name'],
                                        virtual_machine['role_name']):
                if db_adapter.count(UserResource,
                                    user_template_id=self.user_template.id,
                                    type=VIRTUAL_MACHINE,
                                    name=virtual_machine['role_name'],
                                    cloud_service_id=cs.id) == 0:
                    m = '%s %s exist but not created by this user template before' % \
                        (VIRTUAL_MACHINE, virtual_machine['role_name'])
                    user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, FAIL, m)
                    vm_endpoint_rollback(cs)
                    log.error(m)
                    return False
                else:
                    m = '%s %s exist and created by this user template before' % \
                        (VIRTUAL_MACHINE, virtual_machine['role_name'])
                    user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, END, m)
                    vm_endpoint_rollback(cs)
                    log.debug(m)
            else:
                # delete old virtual machine info in database, cascade delete old vm endpoint and old vm config
                db_adapter.delete_all_objects(UserResource,
                                              type=VIRTUAL_MACHINE,
                                              name=virtual_machine['role_name'],
                                              cloud_service_id=cs.id)
                db_adapter.commit()
                try:
                    result = self.service.add_role(cloud_service['service_name'],
                                                   deployment['deployment_name'],
                                                   virtual_machine['role_name'],
                                                   config,
                                                   os_hd,
                                                   network_config=network,
                                                   role_size=virtual_machine['role_size'])
                except Exception as e:
                    user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, FAIL, e.message)
                    vm_endpoint_rollback(cs)
                    log.error(e)
                    return False
                # make sure async operation succeeds
                if not wait_for_async(self.service, result.request_id, ASYNC_TICK, ASYNC_LOOP):
                    m = WAIT_FOR_ASYNC + ' ' + FAIL
                    user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, FAIL, m)
                    vm_endpoint_rollback(cs)
                    log.error(m)
                    return False
                # make sure role is ready
                if not self.wait_for_role(cloud_service['service_name'],
                                          deployment['deployment_name'],
                                          virtual_machine['role_name'],
                                          VIRTUAL_MACHINE_TICK,
                                          VIRTUAL_MACHINE_LOOP):
                    m = '%s %s created but not ready' % (VIRTUAL_MACHINE, virtual_machine['role_name'])
                    user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, FAIL, m)
                    vm_endpoint_rollback(cs)
                    log.error(m)
                    return False
                else:
                    user_resource_commit(self.user_template,
                                         VIRTUAL_MACHINE,
                                         virtual_machine['role_name'],
                                         RUNNING,
                                         cs.id)
                    user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, END)
                    self.__vm_info_helper(cs,
                                          cloud_service['service_name'],
                                          deployment['deployment_name'],
                                          virtual_machine['role_name'])
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
                m = create_deployment_error[0] % (DEPLOYMENT, deployment_name, e.message)
                commit_azure_log(experiment, ALOperation.CREATE_DEPLOYMENT, ALStatus.FAIL, m, 0)
                m = create_virtual_machine_error[0] % (VIRTUAL_MACHINE, virtual_machine_name, e.message)
                commit_azure_log(experiment, ALOperation.CREATE_VIRTUAL_MACHINE, ALStatus.FAIL, m, 0)
                log.error(e)
                return False
            # make sure async operation succeeds
            if not self.service.wait_for_async(result.request_id, ASYNC_TICK, ASYNC_LOOP):
                m = create_deployment_error[1] % (DEPLOYMENT, deployment_name)
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
                m = create_deployment_error[2] % (DEPLOYMENT, deployment_name)
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
            if not self.wait_for_role(cloud_service['service_name'],
                                      deployment['deployment_name'],
                                      virtual_machine['role_name'],
                                      VIRTUAL_MACHINE_TICK,
                                      VIRTUAL_MACHINE_LOOP):
                m = '%s %s created but not ready' % (VIRTUAL_MACHINE, virtual_machine['role_name'])
                user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, FAIL, m)
                vm_endpoint_rollback(cs)
                log.error(m)
                return False
            else:
                user_resource_commit(self.user_template,
                                     VIRTUAL_MACHINE,
                                     virtual_machine['role_name'],
                                     RUNNING,
                                     cs.id)
                user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, END)
                self.__vm_info_helper(cs,
                                      cloud_service['service_name'],
                                      deployment['deployment_name'],
                                      virtual_machine['role_name'])

        return True

    # --------------------------------------------helper function-------------------------------------------- #

    def __vm_info_helper(self, cs, cs_name, dm_name, vm_name):
        """
        Help to complete vm info
        :param cs:
        :param cs_name:
        :param dm_name:
        :param vm_name:
        :return:
        """
        # associate vm endpoint with specific vm
        vm = db_adapter.find_first_object(UserResource,
                                          user_template=self.user_template,
                                          type=VIRTUAL_MACHINE,
                                          name=vm_name,
                                          cloud_service_id=cs.id)
        vm_endpoint_update(cs, vm)
        # commit vm config
        deploy = self.service.get_deployment_by_name(cs_name, dm_name)
        for role in deploy.role_instance_list:
            # to get private ip
            if role.role_name == vm_name:
                public_ip = None
                # to get public ip
                if role.instance_endpoints is not None:
                    public_ip = role.instance_endpoints.instance_endpoints[0].vip
                vm_config_commit(vm, deploy.url, public_ip, role.ip_address)
                break