__author__ = 'Yifu Huang'

from src.app.cloudABC import CloudABC
from src.app.database import *
from src.app.log import *
from azure.servicemanagement import *
import json
import time
import os
import commands
import datetime


class AzureImpl(CloudABC):
    """
    Azure cloud service management
    For logic: manage only resources created by this program itself
    For template: one storage account, one container, one cloud service, one deployment,
    multiple virtual machines (Windows/Linux), multiple input endpoints
    """

    def __init__(self):
        super(AzureImpl, self).__init__()
        self.sms = None
        self.user_template = None
        self.template_config = None
        self.update_template_config = None

    def register(self, name, email, subscription_id, management_host):
        """
        Create user info and key according to given information:
        1. Create user info
        2. Create cer and pem file
        :param name:
        :param email:
        :param subscription_id:
        :param management_host:
        :return: user info
        """
        user_info = super(AzureImpl, self).register(name, email)
        certificates_dir = os.path.dirname(__file__) + os.path.sep + 'certificates'
        # make sure certificate dir exists
        if not os.path.isdir(certificates_dir):
            os.mkdir(certificates_dir)
        base_url = '%s/%s-%s' % (certificates_dir, user_info.id, subscription_id)
        pem_url = base_url + '.pem'
        # avoid duplicate pem generation
        if not os.path.isfile(pem_url):
            pem_command = 'openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout %s -out %s -batch' %\
                          (pem_url, pem_url)
            commands.getstatusoutput(pem_command)
        else:
            log.debug('%s exist' % pem_url)
        cert_url = base_url + '.cer'
        # avoid duplicate cer generation
        if not os.path.isfile(cert_url):
            cert_command = 'openssl x509 -inform pem -in %s -outform der -out %s' % (pem_url, cert_url)
            commands.getstatusoutput(cert_command)
        else:
            log.debug('%s exist' % cert_url)
        # avoid duplicate user key
        user_key = UserKey.query.filter_by(user_info=user_info).first()
        if user_key is None:
            user_key = UserKey(user_info, cert_url, pem_url, subscription_id, management_host)
            db.session.add(user_key)
            db.session.commit()
        else:
            log.debug('user key [%d] has registered' % user_key.id)
        return user_info

    def connect(self, user_info):
        """
        Connect to azure service management service according to given user info
        :param user_info:
        :return: Whether service management service is connected
        """
        user_key = UserKey.query.filter_by(user_info=user_info).first()
        # make sure user key exists
        if user_key is None:
            log.debug('user [%d] not exist' % user_info.id)
            return False
        try:
            self.sms = ServiceManagementService(user_key.subscription_id, user_key.pem_url, user_key.management_host)
        except Exception as e:
            log.debug(e)
            return False
        return True

    def create(self, user_template):
        """
        Create virtual machines according to given user template (assume all fields needed are in template)
        1. Load template from json into dictionary
        2. If storage account not exist, then create it
        3. If cloud service not exist, then create it
        4. If deployment not exist, then create virtual machine with deployment
           Else add virtual machine to deployment
        :param user_template:
        :return: Whether a virtual machines are created
        """
        if not self._load_template(user_template):
            return False
        if not self._create_storage_account():
            return False
        if not self._create_cloud_service():
            return False
        if not self._create_virtual_machines():
            return False
        return True

    def update(self, user_template, update_template):
        """
        Update virtual machines created by user template according to given update template
        (assume all fields needed are in template, resources in user template and update template are the same)
        Currently support only network config and role size
        :param user_template:
        :param update_template:
        :return: Whether virtual machines are updated
        """
        if not self._load_template(user_template):
            return False
        if not self._load_update_template(update_template):
            return False
        self._user_operation_commit('update', 'start')
        cloud_service = self.template_config['cloud_service']
        deployment = self.template_config['deployment']
        virtual_machines = self.template_config['virtual_machines']
        cs = UserResource.query.filter_by(user_template=self.user_template,
                                          type='cloud service',
                                          name=cloud_service['service_name'],
                                          status='Running').first()
        # make sure cloud service exist in database
        if cs is None:
            m = 'cloud service %s not exist in database' % cloud_service['service_name']
            self._user_operation_commit('update', 'fail', m)
            log.debug(m)
            return False
        # make sure cloud service exist in azure
        if not self._hosted_service_exists(cloud_service['service_name']):
            m = 'cloud service %s not exist in azure' % cloud_service['service_name']
            self._user_operation_commit('update', 'fail', m)
            log.debug(m)
            return False
        # make sure deployment exist in database
        if UserResource.query.filter_by(user_template=self.user_template,
                                        type='deployment',
                                        name=deployment['deployment_name'],
                                        status='Running',
                                        cloud_service_id=cs.id).count() == 0:
            m = 'deployment %s not exist in database' % deployment['deployment_name']
            self._user_operation_commit('update', 'fail', m)
            log.debug(m)
            return False
        # make sure deployment exist in azure
        if not self._deployment_exists(cloud_service['service_name'], deployment['deployment_name']):
            m = 'deployment %s not exist in azure' % deployment['deployment_name']
            self._user_operation_commit('update', 'fail', m)
            log.debug(m)
            return False
        for virtual_machine in virtual_machines:
            # make sure virtual machine exist in database
            if UserResource.query.filter_by(user_template=self.user_template,
                                            type='virtual machine',
                                            name=virtual_machine['role_name'],
                                            status='Running',
                                            cloud_service_id=cs.id).count() == 0:
                m = 'virtual machine %s not exist in database' % virtual_machine['role_name']
                self._user_operation_commit('update', 'fail', m)
                log.debug(m)
                return False
            # make sure virtual machine exist in azure
            if not self._role_exists(cloud_service['service_name'], deployment['deployment_name'],
                                     virtual_machine['role_name']):
                m = 'virtual machine %s not exist in azure' % virtual_machine['role_name']
                self._user_operation_commit('update', 'fail', m)
                log.debug(m)
                return False
        # now check done, begin update
        update_virtual_machines = self.update_template_config['virtual_machines']
        for update_virtual_machine in update_virtual_machines:
            self._user_operation_commit('update_virtual_machine', 'start')
            network_config = update_virtual_machine['network_config']
            network = ConfigurationSet()
            network.configuration_set_type = network_config['configuration_set_type']
            input_endpoints = network_config['input_endpoints']
            vm = UserResource.query.filter_by(user_template=self.user_template, type='virtual machine',
                                              name=update_virtual_machine['role_name'], status='Running',
                                              cloud_service_id=cs.id).first()
            old_endpoints = VMEndpoint.query.filter_by(virtual_machine=vm).all()
            new_endpoints = []
            for input_endpoint in input_endpoints:
                endpoint = VMEndpoint(input_endpoint['name'], input_endpoint['protocol'],
                                      input_endpoint['port'], input_endpoint['local_port'], cs, vm)
                new_endpoints.append(endpoint)
                network.input_endpoints.input_endpoints.append(
                    ConfigurationSetInputEndpoint(input_endpoint['name'], input_endpoint['protocol'],
                                                  input_endpoint['port'], input_endpoint['local_port']))
            try:
                result = self.sms.update_role(cloud_service['service_name'], deployment['deployment_name'],
                                              update_virtual_machine['role_name'], network_config=network,
                                              role_size=update_virtual_machine['role_size'])
            except Exception as e:
                self._user_operation_commit('update_virtual_machine', 'fail', e.message)
                log.debug(e)
                return False
            # make sure async operation succeeds
            if not self._wait_for_async(result.request_id, 30, 30):
                m = '_wait_for_async fail'
                self._user_operation_commit('update_virtual_machine', 'fail', m)
                log.debug(m)
                return False
            # make sure role is ready
            if not self._wait_for_role(cloud_service['service_name'], deployment['deployment_name'],
                                       update_virtual_machine['role_name'], 30, 30):
                m = 'virtual machine %s updated but not ready' % update_virtual_machine['role_name']
                self._user_operation_commit('update_virtual_machine', 'fail', m)
                log.debug(m)
                return False
            role = self.sms.get_role(cloud_service['service_name'], deployment['deployment_name'],
                                     update_virtual_machine['role_name'])
            # make sure virtual machine is updated
            if role.role_size != update_virtual_machine['role_size'] or not self._cmp_network_config(
                    role.configuration_sets, network):
                m = 'virtual machine %s updated but failed' % update_virtual_machine['role_name']
                self._user_operation_commit('update_virtual_machine', 'fail', m)
                log.debug(m)
                return False
            for old_endpoint in old_endpoints:
                db.session.delete(old_endpoint)
            for new_endpoint in new_endpoints:
                db.session.add(new_endpoint)
            db.session.commit()
            self._user_operation_commit('update_virtual_machine', 'end')
        self._user_operation_commit('update', 'end')
        self.update_template_config = None
        return True

    def delete(self, user_template):
        """
        Delete a virtual machine according to given user template (assume all fields needed are in template)
        If deployment has only a virtual machine, then delete a virtual machine with deployment
        Else delete a virtual machine from deployment
        :param user_template:
        :return: Whether a virtual machine is deleted
        """
        if not self._load_template(user_template):
            return False
        self._user_operation_commit('delete', 'start')
        cloud_service = self.template_config['cloud_service']
        deployment = self.template_config['deployment']
        virtual_machines = self.template_config['virtual_machines']
        # make sure cloud service exist in database
        cs = UserResource.query.filter_by(user_template=self.user_template, type='cloud service',
                                          name=cloud_service['service_name'], status='Running').first()
        if cs is None:
            m = 'cloud service %s not exist in database' % cloud_service['service_name']
            self._user_operation_commit('delete', 'fail', m)
            log.debug(m)
            return False
        # make sure cloud service exist in azure
        if not self._hosted_service_exists(cloud_service['service_name']):
            m = 'cloud service %s not exist in azure' % cloud_service['service_name']
            self._user_operation_commit('delete', 'fail', m)
            log.debug(m)
            return False
        # make sure deployment exist in database
        if UserResource.query.filter_by(user_template=self.user_template,
                                        type='deployment',
                                        name=deployment['deployment_name'],
                                        status='Running', cloud_service_id=cs.id).count() == 0:
            m = 'deployment %s not exist in database' % deployment['deployment_name']
            self._user_operation_commit('delete', 'fail', m)
            log.debug(m)
            return False
        # make sure deployment exist in azure
        if not self._deployment_exists(cloud_service['service_name'], deployment['deployment_name']):
            m = 'deployment %s not exist in azure' % deployment['deployment_name']
            self._user_operation_commit('delete', 'fail', m)
            log.debug(m)
            return False
        for virtual_machine in virtual_machines:
            # make sure virtual machine exist in database
            if UserResource.query.filter_by(user_template=self.user_template,
                                            type='virtual machine',
                                            name=virtual_machine['role_name'],
                                            status='Running', cloud_service_id=cs.id).count() == 0:
                m = 'virtual machine %s not exist in database' % virtual_machine['role_name']
                self._user_operation_commit('delete', 'fail', m)
                log.debug(m)
                return False
            # make sure virtual machine exist in azure
            if not self._role_exists(cloud_service['service_name'], deployment['deployment_name'],
                                     virtual_machine['role_name']):
                m = 'virtual machine %s not exist in azure' % virtual_machine['role_name']
                self._user_operation_commit('delete', 'fail', m)
                log.debug(m)
                return False
        for virtual_machine in virtual_machines:
            deploy = self.sms.get_deployment_by_name(cloud_service['service_name'], deployment['deployment_name'])
            # whether only one virtual machine in deployment
            if len(deploy.role_instance_list) == 1:
                self._user_operation_commit('delete_deployment', 'start')
                self._user_operation_commit('delete_virtual_machine', 'start')
                try:
                    result = self.sms.delete_deployment(cloud_service['service_name'], deployment['deployment_name'])
                except Exception as e:
                    self._user_operation_commit('delete_deployment', 'fail', e.message)
                    self._user_operation_commit('delete_virtual_machine', 'fail', e.message)
                    log.debug(e)
                    return False
                # make sure async operation succeeds
                if not self._wait_for_async(result.request_id, 30, 30):
                    m = '_wait_for_async fail'
                    self._user_operation_commit('delete_deployment', 'fail', m)
                    self._user_operation_commit('delete_virtual_machine', 'fail', m)
                    log.debug(m)
                    return False
                # make sure deployment not exist
                if self._deployment_exists(cloud_service['service_name'], deployment['deployment_name']):
                    m = 'deployment %s deleted but failed' % deployment['deployment_name']
                    self._user_operation_commit('delete_deployment', 'fail', m)
                    log.debug(m)
                    return False
                else:
                    dm = UserResource.query.filter_by(user_template=user_template, type='deployment',
                                                      name=deployment['deployment_name'], status='Running',
                                                      cloud_service_id=cs.id).first()
                    dm.status = 'Deleted'
                    db.session.commit()
                    self._user_operation_commit('delete_deployment', 'end')
                # make sure virtual machine not exist
                if self._role_exists(cloud_service['service_name'], deployment['deployment_name'],
                                     virtual_machine['role_name']):
                    m = 'virtual machine %s deleted but failed' % virtual_machine['role_name']
                    self._user_operation_commit('delete_virtual_machine', 'fail', m)
                    log.debug(m)
                    return False
                else:
                    vm = UserResource.query.filter_by(user_template=user_template, type='virtual machine',
                                                      name=virtual_machine['role_name'], status='Running',
                                                      cloud_service_id=cs.id).first()
                    VMEndpoint.query.filter_by(virtual_machine=vm).delete()
                    VMConfig.query.filter_by(virtual_machine=vm).delete()
                    vm.status = 'Deleted'
                    db.session.commit()
                    self._user_operation_commit('delete_virtual_machine', 'end')
            else:
                self._user_operation_commit('delete_virtual_machine', 'start')
                try:
                    result = self.sms.delete_role(cloud_service['service_name'], deployment['deployment_name'],
                                                  virtual_machine['role_name'])
                except Exception as e:
                    self._user_operation_commit('delete_virtual_machine', 'fail', e.message)
                    log.debug(e)
                    return False
                # make sure async operation succeeds
                if not self._wait_for_async(result.request_id, 30, 30):
                    m = '_wait_for_async fail'
                    self._user_operation_commit('delete_virtual_machine', 'fail', m)
                    log.debug(m)
                    return False
                # make sure virtual machine not exist
                if self._role_exists(cloud_service['service_name'], deployment['deployment_name'],
                                     virtual_machine['role_name']):
                    m = 'virtual machine %s deleted but failed' % virtual_machine['role_name']
                    self._user_operation_commit('delete_virtual_machine', 'fail', m)
                    log.debug(m)
                    return False
                else:
                    vm = UserResource.query.filter_by(user_template=user_template, type='virtual machine',
                                                      name=virtual_machine['role_name'], status='Running',
                                                      cloud_service_id=cs.id).first()
                    VMEndpoint.query.filter_by(virtual_machine=vm).delete()
                    VMConfig.query.filter_by(virtual_machine=vm).delete()
                    vm.status = 'Deleted'
                    db.session.commit()
                    self._user_operation_commit('delete_virtual_machine', 'end')
        self._user_operation_commit('delete', 'end')
        return True

    # --------------------------------------------helper function-------------------------------------------- #

    def _load_template(self, user_template):
        """
        Load json based template into dictionary
        :param user_template:
        :return:
        """
        self.user_template = user_template
        # make sure template url exists
        if os.path.isfile(user_template.template.url):
            try:
                self.template_config = json.load(file(user_template.template.url))
            except Exception as e:
                log.debug('ugly json format: %s' % e)
                return False
        else:
            log.debug('%s not exist' % user_template.template.url)
            return False
        return True

    def _create_storage_account(self):
        """
        If storage account not exist, then create it
        Else check whether it created by this function before
        :return:
        """
        self._user_operation_commit('_create_storage_account', 'start')
        storage_account = self.template_config['storage_account']
        # avoid duplicate storage account
        if not self._storage_account_exists(storage_account['service_name']):
            try:
                result = self.sms.create_storage_account(storage_account['service_name'],
                                                         storage_account['description'],
                                                         storage_account['label'],
                                                         location=storage_account['location'])
            except Exception as e:
                self._user_operation_commit('_create_storage_account', 'fail', e.message)
                log.debug(e)
                return False
            # make sure async operation succeeds
            if not self._wait_for_async(result.request_id, 30, 30):
                m = '_wait_for_async fail'
                self._user_operation_commit('_create_storage_account', 'fail', m)
                log.debug(m)
                return False
            # make sure storage account exists
            if not self._storage_account_exists(storage_account['service_name']):
                m = 'storage account %s created but not exist' % storage_account['service_name']
                self._user_operation_commit('_create_storage_account', 'fail', m)
                log.debug(m)
                return False
            else:
                self._user_resource_commit('storage account', storage_account['service_name'], 'Running')
                self._user_operation_commit('_create_storage_account', 'end')
        else:
            # check whether storage account created by this function before
            if UserResource.query.filter_by(user_template=self.user_template,
                                            type='storage account',
                                            name=storage_account['service_name'],
                                            status='Running').count() == 0:
                m = 'storage account %s exist but not created by this function before' %\
                    storage_account['service_name']
                self._user_operation_commit('_create_storage_account', 'fail', m)
                log.debug(m)
                return False
            else:
                m = 'storage account %s exist and created by this function before' % storage_account['service_name']
                self._user_operation_commit('_create_storage_account', 'end', m)
                log.debug(m)
        return True

    def _user_operation_commit(self, operation, status, note=None):
        """
        Commit user operation to database
        :param operation:
        :param status:
        :param note:
        :return:
        """
        user_operation = UserOperation(self.user_template, operation, status, note)
        db.session.add(user_operation)
        db.session.commit()

    def _storage_account_exists(self, name):
        """
        Check whether specific storage account exist
        :param name:
        :return:
        """
        try:
            props = self.sms.get_storage_account_properties(name)
        except Exception as e:
            if e.message != 'Not found (Not Found)':
                log.debug('storage account %s: %s' % (name, e))
            return False
        return props is not None

    def _wait_for_async(self, request_id, second_per_loop, loop):
        """
        Wait for async operation, up tp second_per_loop * loop
        :param request_id:
        :return:
        """
        count = 0
        result = self.sms.get_operation_status(request_id)
        while result.status == 'InProgress':
            log.debug('_wait_for_async [%s] loop count [%d]' % (request_id, count))
            count += 1
            if count > loop:
                log.debug('Timed out waiting for async operation to complete.')
                return False
            time.sleep(second_per_loop)
            result = self.sms.get_operation_status(request_id)
        if result.status != 'Succeeded':
            log.debug(vars(result))
            if result.error:
                log.debug(result.error.code)
                log.debug(vars(result.error))
            log.debug('Asynchronous operation did not succeed.')
            return False
        return True

    def _user_resource_commit(self, type, name, status, cs_id=None):
        """
        Commit user resource to database
        :param type:
        :param name:
        :param status:
        :return:
        """
        user_resource = UserResource(self.user_template, type, name, status, cs_id)
        db.session.add(user_resource)
        db.session.commit()

    def _create_cloud_service(self):
        """
        If cloud service not exist, then create it
        Else check whether it created by this function before
        :return:
        """
        self._user_operation_commit('_create_cloud_service', 'start')
        cloud_service = self.template_config['cloud_service']
        # avoid duplicate cloud service
        if not self._hosted_service_exists(cloud_service['service_name']):
            try:
                self.sms.create_hosted_service(service_name=cloud_service['service_name'],
                                               label=cloud_service['label'],
                                               location=cloud_service['location'])
            except Exception as e:
                self._user_operation_commit('_create_cloud_service', 'fail', e.message)
                log.debug(e)
                return False
            # make sure cloud service is created
            if not self._hosted_service_exists(cloud_service['service_name']):
                m = 'cloud service %s created but not exist' % cloud_service['service_name']
                self._user_operation_commit('_create_cloud_service', 'fail', m)
                log.debug(m)
                return False
            else:
                self._user_resource_commit('cloud service',  cloud_service['service_name'], 'Running')
                self._user_operation_commit('_create_cloud_service', 'end')
        else:
            # check whether cloud service created by this function before
            if UserResource.query.filter_by(user_template=self.user_template,
                                            type='cloud service',
                                            name=cloud_service['service_name'],
                                            status='Running').count() == 0:
                m = 'cloud service %s exist but not created by this function before' % cloud_service['service_name']
                self._user_operation_commit('_create_cloud_service', 'fail', m)
                log.debug(m)
                return False
            else:
                m = 'cloud service %s exist and created by this function before' % cloud_service['service_name']
                self._user_operation_commit('_create_cloud_service', 'end', m)
                log.debug(m)
        return True

    def _hosted_service_exists(self, name):
        """
        Check whether specific cloud service exist
        :param name:
        :return:
        """
        try:
            props = self.sms.get_hosted_service_properties(name)
        except Exception as e:
            if e.message != 'Not found (Not Found)':
                log.debug('cloud service %s: %s' % (name, e))
            return False
        return props is not None

    def _create_virtual_machines(self):
        """
        1. If deployment not exist, then create virtual machine with deployment
           Else check whether it created by this function before
        2. If deployment created by this function before and virtual machine not exist,
            then add virtual machine to deployment
           Else check whether virtual machine created by this function before
        :return:
        """
        self._user_operation_commit('_create_virtual_machines', 'start')
        storage_account = self.template_config['storage_account']
        container = self.template_config['container']
        cloud_service = self.template_config['cloud_service']
        deployment = self.template_config['deployment']
        virtual_machines = self.template_config['virtual_machines']
        cs = UserResource.query.filter_by(user_template=self.user_template, type='cloud service',
                                          name=cloud_service['service_name'], status='Running').first()
        if cs is None:
            m = 'cloud service %s not running in database now' % cloud_service['service_name']
            self._user_operation_commit('_create_virtual_machines', 'fail', m)
            log.debug(m)
            return False
        for virtual_machine in virtual_machines:
            self._user_operation_commit('_create_virtual_machines_deployment', 'start')
            self._user_operation_commit('_create_virtual_machines_role', 'start')
            system_config = virtual_machine['system_config']
            # check whether virtual machine is Windows or Linux
            if system_config['os_family'] == 'Windows':
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
                    if not self._wait_for_async(result.request_id, 30, 30):
                        m = '_wait_for_async fail'
                        self._user_operation_commit('_create_virtual_machines_role', 'fail', m)
                        self._vm_endpoint_rollback(cs)
                        log.debug(m)
                        return False
                    # make sure role is ready
                    if not self._wait_for_role(cloud_service['service_name'], deployment['deployment_name'],
                                               virtual_machine['role_name'], 30, 30):
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
                if not self._wait_for_async(result.request_id, 30, 30):
                    m = '_wait_for_async fail'
                    self._user_operation_commit('_create_virtual_machines_deployment', 'fail', m)
                    self._user_operation_commit('_create_virtual_machines_role', 'fail', m)
                    self._vm_endpoint_rollback(cs)
                    log.debug(m)
                    return False
                # make sure deployment is ready
                if not self._wait_for_deployment(cloud_service['service_name'], deployment['deployment_name'], 30, 30):
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
                                           virtual_machine['role_name'], 30, 30):
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

    def _vm_endpoint_commit(self, name, protocol, port, local_port, cs):
        """
        Commit vm endpoint to database before create vm
        :param name:
        :param protocol:
        :param port:
        :param local_port:
        :param cs:
        :return:
        """
        vm_endpoint = VMEndpoint(name, protocol, port, local_port, cs)
        db.session.add(vm_endpoint)
        db.session.commit()

    def _deployment_exists(self, service_name, deployment_name):
        """
        Check whether specific deployment exist
        :param service_name:
        :param deployment_name:
        :return:
        """
        try:
            props = self.sms.get_deployment_by_name(service_name, deployment_name)
        except Exception as e:
            if e.message != 'Not found (Not Found)':
                log.debug('deployment %s: %s' % (deployment_name, e))
            return False
        return props is not None

    def _vm_endpoint_rollback(self, cs):
        """
        Rollback vm endpoint in database because no vm created
        :param cs:
        :return:
        """
        VMEndpoint.query.filter_by(cloud_service=cs, virtual_machine=None).delete()
        db.session.commit()

    def _role_exists(self, service_name, deployment_name, role_name):
        """
        Check whether specific virtual machine exist
        :param service_name:
        :param deployment_name:
        :param role_name:
        :return:
        """
        try:
            props = self.sms.get_role(service_name, deployment_name, role_name)
        except Exception as e:
            if e.message != 'Not found (Not Found)':
                log.debug('virtual machine %s: %s' % (role_name, e))
            return False
        return props is not None

    def _vm_endpoint_update(self, cs, vm):
        """
        Update vm endpoint in database after vm created
        :param cs:
        :param vm:
        :return:
        """
        vm_endpoints = VMEndpoint.query.filter_by(cloud_service=cs, virtual_machine=None).all()
        for vm_endpoint in vm_endpoints:
            vm_endpoint.virtual_machine = vm
        db.session.commit()

    def _vm_config_commit(self, vm, dns, public_ip, private_ip):
        """
        Commit vm config to database
        :param vm:
        :return:
        """
        vm_config = VMConfig(vm, dns, public_ip, private_ip)
        db.session.add(vm_config)
        db.session.commit()

    def _wait_for_deployment(self, service_name, deployment_name, second_per_loop, loop, status='Running'):
        """
        Wait for deployment until running
        :param service_name:
        :param deployment_name:
        :param second_per_loop:
        :param loop:
        :param status:
        :return:
        """
        count = 0
        props = self.sms.get_deployment_by_name(service_name, deployment_name)
        while props.status != status:
            log.debug('_wait_for_deployment [%s] loop count: %d' % (deployment_name, count))
            count += 1
            if count > loop:
                log.debug('Timed out waiting for deployment status.')
                return False
            time.sleep(second_per_loop)
            props = self.sms.get_deployment_by_name(service_name, deployment_name)
        return props.status == status

    def _wait_for_role(self, service_name, deployment_name, role_instance_name,
                       second_per_loop, loop, status='ReadyRole'):
        """
        Wait virtual machine until ready
        :param service_name:
        :param deployment_name:
        :param role_instance_name:
        :param second_per_loop:
        :param loop:
        :param status:
        :return:
        """
        count = 0
        props = self.sms.get_deployment_by_name(service_name, deployment_name)
        while self._get_role_instance_status(props, role_instance_name) != status:
            log.debug('_wait_for_role [%s] loop count: %d' % (role_instance_name, count))
            count += 1
            if count > loop:
                log.debug('Timed out waiting for role instance status.')
                return False
            time.sleep(second_per_loop)
            props = self.sms.get_deployment_by_name(service_name, deployment_name)
        return self._get_role_instance_status(props, role_instance_name) == status

    def _get_role_instance_status(self, deployment, role_instance_name):
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

    def _load_update_template(self, update_template):
        """
        Load json based template into dictionary
        :param update_template:
        :return:
        """
        # make sure template url exists
        if os.path.isfile(update_template.template.url):
            try:
                self.update_template_config = json.load(file(update_template.template.url))
            except Exception as e:
                log.debug('ugly json format: %s' % e)
                return False
        else:
            log.debug('%s not exist' % update_template.template.url)
            return False
        return True

    def _cmp_network_config(self, configuration_sets, network2):
        """
        Check whether two network config are the same
        :param configuration_sets:
        :param network2:
        :return:
        """
        for network1 in configuration_sets:
            if network1.configuration_set_type == 'NetworkConfiguration':
                points1 = network1.input_endpoints.input_endpoints
                points1 = sorted(points1, key=lambda point: point.name)
                points2 = network2.input_endpoints.input_endpoints
                points2 = sorted(points2, key=lambda point: point.name)
                if len(points1) != len(points2):
                    return False
                for i in range(len(points1)):
                    if points1[i].name != points2[i].name:
                        return False
                    if points1[i].protocol != points2[i].protocol:
                        return False
                    if points1[i].port != points2[i].port:
                        return False
                    if points1[i].local_port != points2[i].local_port:
                        return False
                return True
        return False