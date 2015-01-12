__author__ = 'Yifu Huang'

from src.app.cloudABC import CloudABC
from database import *
import os
import commands
from src.app.log import *


class AzureImpl(CloudABC):
    def register(self, name, email, subscription_id, management_host):
        user_info = super(AzureImpl, self).register(name, email)
        certificates_dir = os.path.abspath('certificates')
        base_url = '%s/%s-%s' % (certificates_dir, user_info.id, subscription_id)
        pem_url = base_url + '.pem'
        cert_url = base_url + '.cer'
        pem_command = 'openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout %s -out %s -batch' % (pem_url, pem_url)
        pem_command_log = commands.getstatusoutput(pem_command)
        log.debug(pem_command_log)
        cert_command = 'openssl x509 -inform pem -in %s -outform der -out %s' % (pem_url, cert_url)
        cert_command_log = commands.getstatusoutput(cert_command)
        log.debug(cert_command_log)
        user_key = UserKey(user_info, cert_url, pem_url, subscription_id, management_host)
        db.session.add(user_key)
        db.session.commit()
        return user_info