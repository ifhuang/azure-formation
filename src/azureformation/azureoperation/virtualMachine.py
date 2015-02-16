__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.subscription import Subscription
from src.azureformation.azureoperation.utility import (
    T_STORAGE_ACCOUNT,
    T_CONTAINER,
    T_CLOUD_SERVICE,
    T_DEPLOYMENT,
    commit_azure_log
)
from src.azureformation.database import db_adapter
from src.azureformation.database.models import(
    AzureCloudService,
    AzureDeployment,
    AzureVirtualMachine
)
from src.azureformation.enum import ALOperation, ALStatus
import datetime


class VirtualMachine:
    """
    Virtual machine is azure virtual machine with its azure deployment
    """

    def __init__(self, service):
        self.service = service
        self.subscription = Subscription(service)

    def create_virtual_machine(self, template_config, experiment):
        """
        1. If deployment not exist in azure subscription, then create virtual machine with deployment
           Else reuse deployment in azure subscription
        2. If virtual machine not exist in azure subscription, then add virtual machine to deployment
           Else reuse virtual machine in azure subscription
        :return:
        """
        commit_azure_log(self.user_template, CREATE_DEPLOYMENT, START)
        commit_azure_log(self.user_template, CREATE_VIRTUAL_MACHINE, START)
        storage_account = template_config[T_STORAGE_ACCOUNT]
        container = template_config[T_CONTAINER]
        cloud_service = template_config[T_CLOUD_SERVICE]
        deployment = template_config[T_DEPLOYMENT]
        cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service['service_name'])
        system_config = virtual_machine['system_config']
        # check whether virtual machine is Windows or Linux
        if system_config['os_family'] == WINDOWS:
            config = WindowsConfigurationSet(computer_name=system_config['host_name'],
                                             admin_password=system_config['user_password'],
                                             admin_username=system_config['user_name'])
            config.domain_join = None
            config.win_rm = None
        else:
            config = LinuxConfigurationSet(system_config['host_name'],
                                           system_config['user_name'],
                                           system_config['user_password'],
                                           False)
        now = datetime.datetime.now()
        blob = '%s-%s-%s-%s-%s-%s-%s.vhd' % (virtual_machine['source_image_name'],
                                             str(now.year), str(now.month), str(now.day),
                                             str(now.hour), str(now.minute), str(now.second))
        media_link = 'https://%s.%s/%s/%s' % (storage_account['service_name'],
                                              storage_account['url_base'],
                                              container,
                                              blob)
        os_hd = OSVirtualHardDisk(virtual_machine['source_image_name'], media_link)
        network_config = virtual_machine['network_config']
        network = ConfigurationSet()
        network.configuration_set_type = network_config['configuration_set_type']
        input_endpoints = network_config['input_endpoints']
        for input_endpoint in input_endpoints:
            port = int(input_endpoint['local_port'])
            # avoid duplicate vm endpoint under same cloud service
            while db_adapter.count(VMEndpoint, cloud_service_id=cs.id, public_port=port) > 0:
                port = (port + 1) % 65536
            vm_endpoint_commit(input_endpoint['name'],
                               input_endpoint['protocol'],
                               port,
                               input_endpoint['local_port'],
                               cs)
            network.input_endpoints.input_endpoints.append(
                ConfigurationSetInputEndpoint(input_endpoint['name'],
                                              input_endpoint['protocol'],
                                              port,
                                              input_endpoint['local_port']))
        # avoid duplicate deployment
        if self.service.deployment_exists(cloud_service['service_name'], deployment['deployment_name']):
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
            # delete old deployment
            db_adapter.delete_all_objects(UserResource,
                                          type=DEPLOYMENT,
                                          name=deployment['deployment_name'],
                                          cloud_service_id=cs.id)
            # delete old virtual machine info in database, cascade delete old vm endpoint and old vm config
            db_adapter.delete_all_objects(UserResource,
                                          type=VIRTUAL_MACHINE,
                                          name=virtual_machine['role_name'],
                                          cloud_service_id=cs.id)
            db_adapter.commit()
            try:
                result = self.service.create_virtual_machine_deployment(cloud_service['service_name'],
                                                                        deployment['deployment_name'],
                                                                        deployment['deployment_slot'],
                                                                        virtual_machine['label'],
                                                                        virtual_machine['role_name'],
                                                                        config,
                                                                        os_hd,
                                                                        network_config=network,
                                                                        role_size=virtual_machine['role_size'])
            except Exception as e:
                user_operation_commit(self.user_template, CREATE_DEPLOYMENT, FAIL, e.message)
                user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, FAIL, e.message)
                vm_endpoint_rollback(cs)
                log.error(e)
                return False
            # make sure async operation succeeds
            if not wait_for_async(self.service, result.request_id, ASYNC_TICK, ASYNC_LOOP):
                m = WAIT_FOR_ASYNC + ' ' + FAIL
                user_operation_commit(self.user_template, CREATE_DEPLOYMENT, FAIL, m)
                user_operation_commit(self.user_template, CREATE_VIRTUAL_MACHINE, FAIL, m)
                vm_endpoint_rollback(cs)
                log.error(m)
                return False
            # make sure deployment is ready
            if not self.__wait_for_deployment(cloud_service['service_name'],
                                              deployment['deployment_name'],
                                              DEPLOYMENT_TICK,
                                              DEPLOYMENT_LOOP):
                m = '%s %s created but not ready' % (DEPLOYMENT, deployment['deployment_name'])
                user_operation_commit(self.user_template, CREATE_DEPLOYMENT, FAIL, m)
                vm_endpoint_rollback(cs)
                log.error(m)
                return False
            else:
                user_resource_commit(self.user_template, DEPLOYMENT, deployment['deployment_name'], RUNNING, cs.id)
                user_operation_commit(self.user_template, CREATE_DEPLOYMENT, END)
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

    def wait_for_role(self, service_name, deployment_name, role_instance_name,
                      second_per_loop, loop, status=READY_ROLE):
        """
        Wait virtual machine until ready, up to second_per_loop * loop
        :param service_name:
        :param deployment_name:
        :param role_instance_name:
        :param second_per_loop:
        :param loop:
        :param status:
        :return:
        """
        count = 0
        props = self.service.get_deployment_by_name(service_name, deployment_name)
        while self.__get_role_instance_status(props, role_instance_name) != status:
            log.debug('_wait_for_role [%s] loop count: %d' % (role_instance_name, count))
            count += 1
            if count > loop:
                log.error('Timed out waiting for role instance status.')
                return False
            time.sleep(second_per_loop)
            props = self.service.get_deployment_by_name(service_name, deployment_name)
        return self.__get_role_instance_status(props, role_instance_name) == status

    # --------------------------------------------helper function-------------------------------------------- #

    def __wait_for_deployment(self, service_name, deployment_name, second_per_loop, loop, status=RUNNING):
        """
        Wait for deployment until running, up to second_per_loop * loop
        :param service_name:
        :param deployment_name:
        :param second_per_loop:
        :param loop:
        :param status:
        :return:
        """
        count = 0
        props = self.service.get_deployment_by_name(service_name, deployment_name)
        while props.status != status:
            log.debug('_wait_for_deployment [%s] loop count: %d' % (deployment_name, count))
            count += 1
            if count > loop:
                log.error('Timed out waiting for deployment status.')
                return False
            time.sleep(second_per_loop)
            props = self.service.get_deployment_by_name(service_name, deployment_name)
        return props.status == status

    def __get_role_instance_status(self, deployment, role_instance_name):
        """
        Get virtual machine status
        :param deployment:
        :param role_instance_name:
        :return:
        """
        for role_instance in deployment.role_instance_list:
            if role_instance.instance_name == role_instance_name:
                return role_instance.instance_status
        return None

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