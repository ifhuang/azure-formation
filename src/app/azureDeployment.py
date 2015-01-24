__author__ = 'Yifu Huang'

from src.app.azureUtil import *
from azure.servicemanagement import *


class AzureDeployment:

    def __init__(self, sms, user_template, template_config):
        self.sms = sms
        self.user_template = user_template
        self.template_config = template_config

    def create_virtual_machines(self):
        """
        1. If deployment not exist, then create virtual machine with deployment
           Else check whether it created by this function before
        2. If deployment created by this function before and virtual machine not exist,
            then add virtual machine to deployment
           Else check whether virtual machine created by this function before
        :return:
        """
        user_operation_commit(CREATE_VIRTUAL_MACHINES, START)
        storage_account = self.template_config['storage_account']
        container = self.template_config['container']
        cloud_service = self.template_config['cloud_service']
        deployment = self.template_config['deployment']
        virtual_machines = self.template_config['virtual_machines']
        cs = UserResource.query.filter_by(user_template=self.user_template, type=CLOUD_SERVICE,
                                          name=cloud_service['service_name'], status=RUNNING).first()
        if cs is None:
            m = '%s %s not running in database now' % (CLOUD_SERVICE, cloud_service['service_name'])
            user_operation_commit(CREATE_VIRTUAL_MACHINES, FAIL, m)
            log.debug(m)
            return False
        for virtual_machine in virtual_machines:
            user_operation_commit(CREATE_VIRTUAL_MACHINES_DEPLOYMENT, START)
            user_operation_commit(CREATE_VIRTUAL_MACHINES_ROLE, START)
            system_config = virtual_machine['system_config']
            # check whether virtual machine is Windows or Linux
            if system_config['os_family'] == WINDOWS:
                config = WindowsConfigurationSet(computer_name=system_config['host_name'],
                                                 admin_password=system_config['user_password'],
                                                 admin_username=system_config['user_name'])
                config.domain_join = None
                config.win_rm = None
            else:
                config = LinuxConfigurationSet(system_config['host_name'], system_config['user_name'],
                                               system_config['user_password'], False)
            now = datetime.datetime.now()
            blob = '%s-%s-%s-%s-%s-%s-%s.vhd' % (virtual_machine['source_image_name'],
                                                 str(now.year), str(now.month), str(now.day),
                                                 str(now.hour), str(now.minute), str(now.second))
            media_link = 'https://%s.%s/%s/%s' % (storage_account['service_name'],
                                                  storage_account['url_base'],
                                                  container, blob)
            os_hd = OSVirtualHardDisk(virtual_machine['source_image_name'], media_link)
            network_config = virtual_machine['network_config']
            network = ConfigurationSet()
            network.configuration_set_type = network_config['configuration_set_type']
            input_endpoints = network_config['input_endpoints']
            for input_endpoint in input_endpoints:
                port = int(input_endpoint['local_port'])
                # avoid duplicate vm endpoint under same cloud service
                while VMEndpoint.query.filter_by(cloud_service=cs, public_port=port).count() > 0:
                    port = (port + 1) % 65536
                self._vm_endpoint_commit(input_endpoint['name'], input_endpoint['protocol'],
                                         port, input_endpoint['local_port'], cs)
                network.input_endpoints.input_endpoints.append(
                    ConfigurationSetInputEndpoint(input_endpoint['name'], input_endpoint['protocol'],
                                                  port, input_endpoint['local_port']))
            # avoid duplicate deployment
            if self._deployment_exists(cloud_service['service_name'], deployment['deployment_name']):
                if UserResource.query.filter_by(user_template=self.user_template, type='deployment',
                                                name=deployment['deployment_name'], status='Running',
                                                cloud_service_id=cs.id).count() == 0:
                    m = 'deployment %s exist but not created by this function before' % deployment['deployment_name']
                    self._user_operation_commit('_create_virtual_machines_deployment', 'fail', m)
                    self._vm_endpoint_rollback(cs)
                    log.debug(m)
                    return False
                else:
                    m = 'deployment %s exist and created by this function before' % deployment['deployment_name']
                    self._user_operation_commit('_create_virtual_machines_deployment', 'end', m)
                    log.debug(m)
                # avoid duplicate role
                if self._role_exists(cloud_service['service_name'], deployment['deployment_name'],
                                     virtual_machine['role_name']):
                    if UserResource.query.filter_by(user_template=self.user_template, type='virtual machine',
                                                    name=virtual_machine['role_name'], status='Running',
                                                    cloud_service_id=cs.id).count() == 0:
                        m = 'virtual machine %s exist but not created by this function before' %\
                            virtual_machine['role_name']
                        self._user_operation_commit('_create_virtual_machines_role', 'fail', m)
                        self._vm_endpoint_rollback(cs)
                        log.debug(m)
                        return False
                    else:
                        m = 'virtual machine %s exist and created by this function before' %\
                            virtual_machine['role_name']
                        self._user_operation_commit('_create_virtual_machines_role', 'end', m)
                        self._vm_endpoint_rollback(cs)
                        log.debug(m)
                else:
                    try:
                        result = self.sms.add_role(cloud_service['service_name'], deployment['deployment_name'],
                                                   virtual_machine['role_name'], config, os_hd,
                                                   network_config=network, role_size=virtual_machine['role_size'])
                    except Exception as e:
                        self._user_operation_commit('_create_virtual_machines_role', 'fail', e.message)
                        self._vm_endpoint_rollback(cs)
                        log.debug(e)
                        return False
                    # make sure async operation succeeds
                    if not self._wait_for_async(result.request_id, 30, 60):
                        m = '_wait_for_async fail'
                        self._user_operation_commit('_create_virtual_machines_role', 'fail', m)
                        self._vm_endpoint_rollback(cs)
                        log.debug(m)
                        return False
                    # make sure role is ready
                    if not self._wait_for_role(cloud_service['service_name'], deployment['deployment_name'],
                                               virtual_machine['role_name'], 30, 60):
                        m = 'virtual machine %s created but not ready' % virtual_machine['role_name']
                        self._user_operation_commit('_create_virtual_machines_role', 'fail', m)
                        self._vm_endpoint_rollback(cs)
                        log.debug(m)
                        return False
                    else:
                        self._user_resource_commit('virtual machine', virtual_machine['role_name'], 'Running', cs.id)
                        self._user_operation_commit('_create_virtual_machines_role', 'end')
                        # associate vm endpoint with specific vm
                        vm = UserResource.query.filter_by(user_template=self.user_template, type='virtual machine',
                                                          name=virtual_machine['role_name'], status='Running',
                                                          cloud_service_id=cs.id).first()
                        self._vm_endpoint_update(cs, vm)
                        # commit vm config
                        deploy = self.sms.get_deployment_by_name(cloud_service['service_name'],
                                                                 deployment['deployment_name'])
                        for role in deploy.role_instance_list:
                            # to get private ip
                            if role.role_name == virtual_machine['role_name']:
                                public_ip = None
                                # to get public ip
                                if role.instance_endpoints is not None:
                                    public_ip = role.instance_endpoints.instance_endpoints[0].vip
                                self._vm_config_commit(vm, deploy.url, public_ip, role.ip_address)
                                break
            else:
                try:
                    result = self.sms.create_virtual_machine_deployment(cloud_service['service_name'],
                                                                        deployment['deployment_name'],
                                                                        deployment['deployment_slot'],
                                                                        virtual_machine['label'],
                                                                        virtual_machine['role_name'],
                                                                        config,
                                                                        os_hd,
                                                                        network_config=network,
                                                                        role_size=virtual_machine['role_size'])
                except Exception as e:
                    self._user_operation_commit('_create_virtual_machines_deployment', 'fail', e.message)
                    self._user_operation_commit('_create_virtual_machines_role', 'fail', e.message)
                    self._vm_endpoint_rollback(cs)
                    log.debug(e)
                    return False
                # make sure async operation succeeds
                if not self._wait_for_async(result.request_id, 30, 60):
                    m = '_wait_for_async fail'
                    self._user_operation_commit('_create_virtual_machines_deployment', 'fail', m)
                    self._user_operation_commit('_create_virtual_machines_role', 'fail', m)
                    self._vm_endpoint_rollback(cs)
                    log.debug(m)
                    return False
                # make sure deployment is ready
                if not self._wait_for_deployment(cloud_service['service_name'], deployment['deployment_name'], 30, 60):
                    m = 'deployment %s created but not ready' % deployment['deployment_name']
                    self._user_operation_commit('_create_virtual_machines_deployment', 'fail', m)
                    self._vm_endpoint_rollback(cs)
                    log.debug(m)
                    return False
                else:
                    self._user_resource_commit('deployment', deployment['deployment_name'], 'Running', cs.id)
                    self._user_operation_commit('_create_virtual_machines_deployment', 'end')
                # make sure role is ready
                if not self._wait_for_role(cloud_service['service_name'], deployment['deployment_name'],
                                           virtual_machine['role_name'], 30, 60):
                    m = 'virtual machine %s created but not ready' % virtual_machine['role_name']
                    self._user_operation_commit('_create_virtual_machines_role', 'fail', m)
                    self._vm_endpoint_rollback(cs)
                    log.debug(m)
                    return False
                else:
                    self._user_resource_commit('virtual machine', virtual_machine['role_name'], 'Running', cs.id)
                    self._user_operation_commit('_create_virtual_machines_role', 'end')
                    # associate vm endpoint with specific vm
                    vm = UserResource.query.filter_by(user_template=self.user_template, type='virtual machine',
                                                      name=virtual_machine['role_name'], status='Running',
                                                      cloud_service_id=cs.id).first()
                    self._vm_endpoint_update(cs, vm)
                    # commit vm config
                    deploy = self.sms.get_deployment_by_name(cloud_service['service_name'],
                                                             deployment['deployment_name'])
                    for role in deploy.role_instance_list:
                        # to get private ip
                        if role.role_name == virtual_machine['role_name']:
                            public_ip = None
                            # to get public ip
                            if role.instance_endpoints is not None:
                                public_ip = role.instance_endpoints.instance_endpoints[0].vip
                            self._vm_config_commit(vm, deploy.url, public_ip, role.ip_address)
                            break
        self._user_operation_commit('_create_virtual_machines', 'end')
        return True