__author__ = 'Yifu Huang'

from src.app.cloudABC import CloudABC
from src.app.database import *
from src.app.log import *
from azure.servicemanagement import *
import json
import time
import sys
import os
import commands


class AzureImpl(CloudABC):

    def __init__(self):
        super(AzureImpl, self).__init__()
        self.sms = None

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
        certificates_dir = os.path.abspath('certificates')
        # make sure certificate dir is exist
        if not os.path.isdir(certificates_dir):
            os.mkdir(certificates_dir)
        base_url = '%s/%s-%s' % (certificates_dir, user_info.id, subscription_id)
        pem_url = base_url + '.pem'
        # avoid duplicate pem generation
        if not os.path.isfile(pem_url):
            pem_command = 'openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout %s -out %s -batch' % (pem_url,
                                                                                                             pem_url)
            commands.getstatusoutput(pem_command)
        else:
            log.debug('%s is exist' % pem_url)
        cert_url = base_url + '.cer'
        # avoid duplicate cer generation
        if not os.path.isfile(cert_url):
            cert_command = 'openssl x509 -inform pem -in %s -outform der -out %s' % (pem_url, cert_url)
            commands.getstatusoutput(cert_command)
        else:
            log.debug('%s is exist' % cert_url)
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
        # make sure user key is exist
        if user_key is None:
            log.debug('user [%d] is not exist' % user_info.id)
            return False
        try:
            self.sms = ServiceManagementService(user_key.subscription_id, user_key.pem_url, user_key.management_host)
        except Exception as e:
            log.debug(e)
            return False
        return True

    def create_vm(self, user_template):
        """
        Create a virtual machine according to given user template (assume all fields needed are in template)
        1. If cloud service is not exist, then create it
        2. If deployment is not exist, then create a virtual machine with deployment, else add a virtual machine to
        deployment
        Currently support only Linux
        :param user_template:
        :return: Whether a virtual machine is created
        """
        # make sure template url is exist
        if os.path.isfile(user_template.template.url):
            try:
                template_config = json.load(file(user_template.template.url))
            except Exception as e:
                log.debug('ugly json format: %s' % e)
                return False
        else:
            log.debug('%s is not exist' % user_template.template.url)
            return False
        cloud_service = template_config['cloud_service']
        # avoid duplicate cloud service
        if not self._hosted_service_exists(cloud_service['service_name']):
            user_operation = UserOperation(user_template, 'create_hosted_service', 'start')
            db.session.add(user_operation)
            db.session.commit()
            try:
                self.sms.create_hosted_service(service_name=cloud_service['service_name'], label=cloud_service['label'],
                                               location=cloud_service['location'])
            except Exception as e:
                user_operation = UserOperation(user_template, 'create_hosted_service', 'fail')
                db.session.add(user_operation)
                db.session.commit()
                log.debug(e)
                return False
            user_operation = UserOperation(user_template, 'create_hosted_service', 'end')
            db.session.add(user_operation)
            db.session.commit()
            # make sure cloud service is created
            if self._hosted_service_exists(cloud_service['service_name']):
                user_resource = UserResource(user_template.user_info, 'cloud service', cloud_service['service_name'],
                                             'Running')
                db.session.add(user_resource)
                db.session.commit()
            else:
                log.debug('cannot create cloud service %s' % cloud_service['service_name'])
                return False
        else:
            log.debug('cloud service %s is exist' % cloud_service['service_name'])
        virtual_machine = template_config['virtual_machine']
        system_config = virtual_machine['system_config']
        linux_config = LinuxConfigurationSet(system_config['host_name'], system_config['user_name'],
                                             system_config['user_password'], False)
        os_virtual_hard_disk = virtual_machine['os_virtual_hard_disk']
        os_hd = OSVirtualHardDisk(os_virtual_hard_disk['source_image_name'], os_virtual_hard_disk['media_link'])
        network_config = virtual_machine['network_config']
        network = ConfigurationSet()
        network.configuration_set_type = network_config['configuration_set_type']
        input_endpoints = network_config['input_endpoints']
        for input_endpoint in input_endpoints:
            network.input_endpoints.input_endpoints.append(ConfigurationSetInputEndpoint(input_endpoint['name'],
                                                                                         input_endpoint['protocol'],
                                                                                         input_endpoint['port'],
                                                                                         input_endpoint['local_port']))
        # avoid duplicate deployment
        if self._deployment_exists(virtual_machine['service_name'], virtual_machine['deployment_name']):
            log.debug('deployment %s is exist' % virtual_machine['deployment_name'])
            # avoid duplicate role
            if self._role_exists(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                 virtual_machine['role_name']):
                log.debug('virtual machine %s is exist' % virtual_machine['role_name'])
            else:
                user_operation = UserOperation(user_template, 'add_role', 'start')
                db.session.add(user_operation)
                db.session.commit()
                try:
                    result = self.sms.add_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                               virtual_machine['role_name'], linux_config, os_hd,
                                               network_config=network, role_size=virtual_machine['role_size'])
                except Exception as e:
                    user_operation = UserOperation(user_template, 'add_role', 'fail')
                    db.session.add(user_operation)
                    db.session.commit()
                    log.debug(e)
                    return False
                self._wait_for_async(result.request_id)
                user_operation = UserOperation(user_template, 'add_role', 'end')
                db.session.add(user_operation)
                db.session.commit()
                # make sure role is ready
                if self._wait_for_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                       virtual_machine['role_name']):
                    user_resource = UserResource(user_template.user_info, 'virtual machine',
                                                 virtual_machine['role_name'], 'Running')
                    db.session.add(user_resource)
                    db.session.commit()
                else:
                    log.debug('virtual machine %s is not ready' % virtual_machine['role_name'])
                    return False
        else:
            user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_deployment', 'start')
            db.session.add(user_operation)
            db.session.commit()
            user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_role', 'start')
            db.session.add(user_operation)
            db.session.commit()
            try:
                result = self.sms.create_virtual_machine_deployment(virtual_machine['service_name'],
                                                                    virtual_machine['deployment_name'],
                                                                    virtual_machine['deployment_slot'],
                                                                    virtual_machine['label'],
                                                                    virtual_machine['role_name'],
                                                                    linux_config,
                                                                    os_hd,
                                                                    network_config=network,
                                                                    role_size=virtual_machine['role_size'])
            except Exception as e:
                user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_deployment', 'fail')
                db.session.add(user_operation)
                db.session.commit()
                user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_role', 'fail')
                db.session.add(user_operation)
                db.session.commit()
                log.debug(e)
                return False
            self._wait_for_async(result.request_id)
            user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_deployment', 'end')
            db.session.add(user_operation)
            db.session.commit()
            user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_role', 'end')
            db.session.add(user_operation)
            db.session.commit()
            # make sure deployment is running
            if self._wait_for_deployment(virtual_machine['service_name'], virtual_machine['deployment_name']):
                user_resource = UserResource(user_template.user_info, 'deployment', virtual_machine['deployment_name'],
                                             'Running')
                db.session.add(user_resource)
                db.session.commit()
            else:
                log.debug('%s is not running' % virtual_machine['deployment_name'])
                return False
            # make sure role is ready
            if self._wait_for_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                   virtual_machine['role_name']):
                user_resource = UserResource(user_template.user_info, 'virtual machine', virtual_machine['role_name'],
                                             'Running')
                db.session.add(user_resource)
                db.session.commit()
            else:
                log.debug('virtual machine %s is not ready' % virtual_machine['role_name'])
                return False
        return True

    def update_vm(self, user_template):
        """
        Update a virtual machine according to given user template (assume all fields needed are in template)
        Currently support only network config and role size
        :param user_template:
        :return: Whether a virtual machine is updated
        """
        # make sure template url is exist
        if os.path.isfile(user_template.template.url):
            try:
                template_config = json.load(file(user_template.template.url))
            except Exception as e:
                log.debug('ugly json format: %s' % e)
                return False
        else:
            log.debug('%s is not exist' % user_template.template.url)
            return False
        cloud_service = template_config['cloud_service']
        # make sure cloud service is exist
        if not self._hosted_service_exists(cloud_service['service_name']):
            log.debug('cloud service %s is not exist' % cloud_service['service_name'])
            return False
        virtual_machine = template_config['virtual_machine']
        # make sure deployment is exist
        if not self._deployment_exists(virtual_machine['service_name'], virtual_machine['deployment_name']):
            log.debug('deployment %s is not exist' % virtual_machine['deployment_name'])
            return False
        # make sure virtual machine is exist
        if not self._role_exists(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                 virtual_machine['role_name']):
            log.debug('virtual machine %s is not exist' % virtual_machine['role_name'])
            return False
        network_config = virtual_machine['network_config']
        network = ConfigurationSet()
        network.configuration_set_type = network_config['configuration_set_type']
        input_endpoints = network_config['input_endpoints']
        for input_endpoint in input_endpoints:
            network.input_endpoints.input_endpoints.append(ConfigurationSetInputEndpoint(input_endpoint['name'],
                                                                                         input_endpoint['protocol'],
                                                                                         input_endpoint['port'],
                                                                                         input_endpoint['local_port']))
        user_operation = UserOperation(user_template, 'update_role', 'start')
        db.session.add(user_operation)
        db.session.commit()
        try:
            result = self.sms.update_role(cloud_service['service_name'], virtual_machine['deployment_name'],
                                          virtual_machine['role_name'], network_config=network,
                                          role_size=virtual_machine['role_size'])
        except Exception as e:
            user_operation = UserOperation(user_template, 'update_role', 'fail')
            db.session.add(user_operation)
            db.session.commit()
            log.debug(e)
            return False
        self._wait_for_async(result.request_id)
        user_operation = UserOperation(user_template, 'update_role', 'end')
        db.session.add(user_operation)
        db.session.commit()
        self._wait_for_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                            virtual_machine['role_name'])
        role = self.sms.get_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                 virtual_machine['role_name'])
        # make sure virtual machine is updated
        if role.role_size != virtual_machine['role_size'] or not self._cmp_network_config(role.configuration_sets,
                                                                                          network):
            log.debug('update virtual machine %s is failed' % virtual_machine['role_name'])
            return False
        return True

    def delete_vm(self, user_template):
        """
        Delete a virtual machine according to given user template (assume all fields needed are in template)
        If deployment has only a virtual machine, then delete a virtual machine with deployment, else delete a virtual
        machine from deployment
        :param user_template:
        :return: Whether a virtual machine is deleted
        """
        # make sure template url is exist
        if os.path.isfile(user_template.template.url):
            try:
                template_config = json.load(file(user_template.template.url))
            except Exception as e:
                log.debug('ugly json format: %s' % e)
                return False
        else:
            log.debug('%s is not exist' % user_template.template.url)
            return False
        cloud_service = template_config['cloud_service']
        # make sure cloud service is exist
        if not self._hosted_service_exists(cloud_service['service_name']):
            log.debug('cloud service %s is not exist' % cloud_service['service_name'])
            return False
        virtual_machine = template_config['virtual_machine']
        # make sure deployment is exist
        if not self._deployment_exists(virtual_machine['service_name'], virtual_machine['deployment_name']):
            log.debug('deployment %s is not exist' % virtual_machine['deployment_name'])
            return False
        # make sure virtual machine is exist
        if not self._role_exists(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                 virtual_machine['role_name']):
            log.debug('virtual machine %s is not exist' % virtual_machine['role_name'])
            return False
        deployment = self.sms.get_deployment_by_name(virtual_machine['service_name'],
                                                     virtual_machine['deployment_name'])
        # whether only one virtual machine in deployment
        if len(deployment.role_instance_list) == 1:
            user_operation = UserOperation(user_template, 'delete_deployment_deployment', 'start')
            db.session.add(user_operation)
            db.session.commit()
            user_operation = UserOperation(user_template, 'delete_deployment_role', 'start')
            db.session.add(user_operation)
            db.session.commit()
            try:
                result = self.sms.delete_deployment(virtual_machine['service_name'],
                                                    virtual_machine['deployment_name'])
            except Exception as e:
                user_operation = UserOperation(user_template, 'delete_deployment_deployment', 'fail')
                db.session.add(user_operation)
                db.session.commit()
                user_operation = UserOperation(user_template, 'delete_deployment_role', 'fail')
                db.session.add(user_operation)
                db.session.commit()
                log.debug(e)
                return False
            self._wait_for_async(result.request_id)
            user_operation = UserOperation(user_template, 'delete_deployment_deployment', 'end')
            db.session.add(user_operation)
            db.session.commit()
            user_operation = UserOperation(user_template, 'delete_deployment_role', 'end')
            db.session.add(user_operation)
            db.session.commit()
            # make sure deployment is not exist
            if not self._deployment_exists(virtual_machine['service_name'], virtual_machine['deployment_name']):
                user_resource = UserResource.query.filter_by(user_info=user_template.user_info,
                                                             type='deployment',
                                                             name=virtual_machine['deployment_name']).first()
                user_resource.status = 'Deleted'
                db.session.commit()
            else:
                log.debug('delete virtual machine %s failed' % virtual_machine['role_name'])
                return False
            # make sure virtual machine is not exist
            if not self._role_exists(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                     virtual_machine['role_name']):
                user_resource = UserResource.query.filter_by(user_info=user_template.user_info,
                                                             type='virtual machine',
                                                             name=virtual_machine['role_name']).first()
                user_resource.status = 'Deleted'
                db.session.commit()
            else:
                log.debug('delete virtual machine %s failed' % virtual_machine['role_name'])
                return False
        else:
            user_operation = UserOperation(user_template, 'delete_role', 'start')
            db.session.add(user_operation)
            db.session.commit()
            try:
                result = self.sms.delete_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                              virtual_machine['role_name'])
            except Exception as e:
                user_operation = UserOperation(user_template, 'delete_role', 'fail')
                db.session.add(user_operation)
                db.session.commit()
                log.debug(e)
                return False
            self._wait_for_async(result.request_id)
            user_operation = UserOperation(user_template, 'delete_role', 'end')
            db.session.add(user_operation)
            db.session.commit()
            # make sure virtual machine is not exist
            if not self._role_exists(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                     virtual_machine['role_name']):
                user_resource = UserResource.query.filter_by(user_info=user_template.user_info,
                                                             type='virtual machine',
                                                             name=virtual_machine['role_name']).first()
                user_resource.status = 'Deleted'
                db.session.commit()
            else:
                log.debug('delete virtual machine %s failed' % virtual_machine['role_name'])
                return False
        return True

    # --------------------------------------------helper function-------------------------------------------- #

    def _hosted_service_exists(self, name):
        try:
            props = self.sms.get_hosted_service_properties(name)
        except Exception as e:
            log.debug('cloud service %s: %s' % (name, e))
            return False
        return props is not None

    def _deployment_exists(self, service_name, deployment_name):
        try:
            props = self.sms.get_deployment_by_name(service_name, deployment_name)
        except Exception as e:
            log.debug('deployment %s: %s' % (deployment_name, e))
            return False
        return props is not None

    def _role_exists(self, service_name, deployment_name, role_name):
        try:
            props = self.sms.get_role(service_name, deployment_name, role_name)
        except Exception as e:
            log.debug('virtual machine %s: %s' % (role_name, e))
            return False
        return props is not None

    def _wait_for_async(self, request_id):
        count = 0
        result = self.sms.get_operation_status(request_id)
        while result.status == 'InProgress':
            log.debug('_wait_for_async loop count: %d' % count)
            count += 1
            if count > 120:
                log.debug('Timed out waiting for async operation to complete.')
                break
            time.sleep(5)
            result = self.sms.get_operation_status(request_id)
        if result.status != 'Succeeded':
            log.debug(vars(result))
            if result.error:
                log.debug(result.error.code)
                log.debug(vars(result.error))
            log.debug('Asynchronous operation did not succeed.')

    def _wait_for_deployment(self, service_name, deployment_name, status='Running'):
        count = 0
        props = self.sms.get_deployment_by_name(service_name, deployment_name)
        while props.status != status:
            log.debug('_wait_for_deployment loop count: %d' % count)
            count += 1
            if count > 120:
                log.debug('Timed out waiting for deployment status.')
                break
            time.sleep(5)
            props = self.sms.get_deployment_by_name(service_name, deployment_name)
        return props.status == status

    def _wait_for_role(self, service_name, deployment_name, role_instance_name, status='ReadyRole'):
        count = 0
        props = self.sms.get_deployment_by_name(service_name, deployment_name)
        while self._get_role_instance_status(props, role_instance_name) != status:
            log.debug('_wait_for_role loop count: %d' % count)
            count += 1
            if count > 120:
                log.debug('Timed out waiting for role instance status.')
                break
            time.sleep(5)
            props = self.sms.get_deployment_by_name(service_name, deployment_name)
        return self._get_role_instance_status(props, role_instance_name) == status

    def _get_role_instance_status(self, deployment, role_instance_name):
        for role_instance in deployment.role_instance_list:
            if role_instance.instance_name == role_instance_name:
                return role_instance.instance_status
        return None

    def _cmp_network_config(self, configuration_sets, network2):
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