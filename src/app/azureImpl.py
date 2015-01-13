__author__ = 'Yifu Huang'

from src.app.cloudABC import CloudABC
from database import *
import os
import commands
from src.app.log import *
from azure.servicemanagement import *
import json
import time
import sys


class AzureImpl(CloudABC):

    def __init__(self):
        super(AzureImpl, self).__init__()
        self.sms = None

    def register(self, name, email, subscription_id, management_host):
        user_info = super(AzureImpl, self).register(name, email)
        certificates_dir = os.path.abspath('certificates')
        # make sure certificate dir is exist
        if not os.path.isdir(certificates_dir):
            log.error('% is not exist' % certificates_dir)
            sys.exit(1)
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
        user_key = UserKey.query.filter_by(user_info=user_info).first()
        self.sms = ServiceManagementService(user_key.subscription_id, user_key.pem_url, user_key.management_host)
        log.debug('service management service connected')

    def create_vm(self, user_template):
        # make sure template url is exist
        if os.path.isfile(user_template.template.url):
            template_config = json.load(file(user_template.template.url))
        else:
            log.error('%s is not exist' % user_template.template.url)
            sys.exit(1)
        # assume all fields needed are in template
        cloud_service = template_config['cloud_service']
        # avoid duplicate cloud service
        if not self._hosted_service_exists(cloud_service['service_name']):
            user_operation = UserOperation(user_template, 'create_hosted_service', 'start')
            db.session.add(user_operation)
            db.session.commit()
            self.sms.create_hosted_service(service_name=cloud_service['service_name'], label=cloud_service['label'],
                                           location=cloud_service['location'])
            # make sure cloud service is created
            if self._hosted_service_exists(cloud_service['service_name']):
                user_operation = UserOperation(user_template, 'create_hosted_service', 'end')
                db.session.add(user_operation)
                db.session.commit()
                user_resource = UserResource(user_template.user_info, 'cloud service', cloud_service['service_name'],
                                             'Running')
                db.session.add(user_resource)
                db.session.commit()
            else:
                log.error('cannot create cloud service %s' % cloud_service['service_name'])
                sys.exit(1)
        else:
            log.debug('cloud service %s is exist' % cloud_service['service_name'])
        virtual_machine = template_config['virtual_machine']
        system_config = virtual_machine['system_config']
        linux_config = LinuxConfigurationSet(system_config['host_name'], system_config['user_name'],
                                             system_config['user_password'], True)
        os_virtual_hard_disk = virtual_machine['os_virtual_hard_disk']
        os_hd = OSVirtualHardDisk(os_virtual_hard_disk['source_image_name'], os_virtual_hard_disk['media_link'])
        # avoid duplicate deployment
        if self._deployment_exists(virtual_machine['service_name'], virtual_machine['deployment_name']):
            # avoid duplicate role
            if self._role_exists(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                 virtual_machine['role_name']):
                log.debug('%s is exist' % virtual_machine['role_name'])
            else:
                user_operation = UserOperation(user_template, 'add_role', 'start')
                db.session.add(user_operation)
                db.session.commit()
                result = self.sms.add_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                           virtual_machine['role_name'], linux_config, os_hd)
                self._wait_for_async(result.request_id)
                # make sure role is ready
                if self._wait_for_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                       virtual_machine['role_name']):
                    user_operation = UserOperation(user_template, 'add_role', 'end')
                    db.session.add(user_operation)
                    db.session.commit()
                    user_resource = UserResource(user_template.user_info, 'virtual machine',
                                                 virtual_machine['role_name'], 'Running')
                    db.session.add(user_resource)
                    db.session.commit()
                else:
                    log.debug('%s is not ready' % virtual_machine['role_name'])
        else:
            user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_deployment', 'start')
            db.session.add(user_operation)
            db.session.commit()
            user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_role', 'start')
            db.session.add(user_operation)
            db.session.commit()
            result = self.sms.create_virtual_machine_deployment(virtual_machine['service_name'],
                                                                virtual_machine['deployment_name'],
                                                                virtual_machine['deployment_slot'],
                                                                virtual_machine['label'],
                                                                virtual_machine['role_name'],
                                                                linux_config,
                                                                os_hd)
            self._wait_for_async(result.request_id)
            # make sure deployment is running
            if self._wait_for_deployment(virtual_machine['service_name'], virtual_machine['deployment_name']):
                user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_deployment', 'end')
                db.session.add(user_operation)
                db.session.commit()
                user_resource = UserResource(user_template.user_info, 'deployment', virtual_machine['deployment_name'],
                                             'Running')
                db.session.add(user_resource)
                db.session.commit()
            else:
                log.debug('%s is not running' % virtual_machine['deployment_name'])
            # make sure role is ready
            if self._wait_for_role(virtual_machine['service_name'], virtual_machine['deployment_name'],
                                   virtual_machine['role_name']):
                user_operation = UserOperation(user_template, 'create_virtual_machine_deployment_role', 'end')
                db.session.add(user_operation)
                db.session.commit()
                user_resource = UserResource(user_template.user_info, 'virtual machine', virtual_machine['role_name'],
                                             'Running')
                db.session.add(user_resource)
                db.session.commit()
            else:
                log.debug('%s is not ready' % virtual_machine['role_name'])

    # --------------------------------------------helper function--------------------------------------------

    def _hosted_service_exists(self, name):
        try:
            props = self.sms.get_hosted_service_properties(name)
            return props is not None
        except:
            return False

    def _deployment_exists(self, service_name, deployment_name):
        try:
            props = self.sms.get_deployment_by_name(
                service_name, deployment_name)
            return props is not None
        except:
            return False

    def _role_exists(self, service_name, deployment_name, role_name):
        try:
            props = self.sms.get_role(service_name, deployment_name, role_name)
            return props is not None
        except:
            return False

    def _wait_for_async(self, request_id):
        count = 0
        result = self.sms.get_operation_status(request_id)
        while result.status == 'InProgress':
            log.debug('_wait_for_async loop')
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
            log.debug('_wait_for_deployment loop')
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
            log.debug('_wait_for_role loop')
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