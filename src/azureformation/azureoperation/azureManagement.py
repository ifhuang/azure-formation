from src.azureformation.functions import (
    get_config,
)
from src.azureformation.log import (
    log,
)
from src.azureformation.database import (
    db_adapter,
)
from src.azureformation.database.models import (
    AzureKey,
    HackathonAzureKey,
)
import os
import commands


class AzureManagement:
    CERT_BASE = get_config('azure.certBase')

    def __init__(self):
        pass

    def create_certificate(self, subscription_id, management_host, hackathon_id):
        """
        1. check certificate dir
        2. generate pem file
        3. generate cert file
        4. add azure key to db
        5. add hackathon azure key to db
        :param subscription_id:
        :param management_host:
        :param hackathon_id:
        :return:
        """

        # make sure certificate dir exists
        if not os.path.isdir(self.CERT_BASE):
            log.debug('certificate dir not exists')
            os.mkdir(self.CERT_BASE)

        base_url = '%s/%s' % (self.CERT_BASE, subscription_id)

        pem_url = base_url + '.pem'
        # avoid duplicate pem generation
        if not os.path.isfile(pem_url):
            pem_command = 'openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout %s -out %s -batch' % \
                          (pem_url, pem_url)
            commands.getstatusoutput(pem_command)
        else:
            log.debug('%s exists' % pem_url)

        cert_url = base_url + '.cer'
        # avoid duplicate cert generation
        if not os.path.isfile(cert_url):
            cert_command = 'openssl x509 -inform pem -in %s -outform der -out %s' % (pem_url, cert_url)
            commands.getstatusoutput(cert_command)
        else:
            log.debug('%s exists' % cert_url)

        azure_key = db_adapter.find_first_object_by(AzureKey,
                                                    cert_url=cert_url,
                                                    pem_url=pem_url,
                                                    subscription_id=subscription_id,
                                                    management_host=management_host)
        # avoid duplicate azure key
        if azure_key is None:
            azure_key = db_adapter.add_object_kwargs(AzureKey,
                                                     cert_url=cert_url,
                                                     pem_url=pem_url,
                                                     subscription_id=subscription_id,
                                                     management_host=management_host)
            db_adapter.commit()
        else:
            log.debug('azure key exists')

        hackathon_azure_key = db_adapter.find_first_object_by(HackathonAzureKey,
                                                              hackathon_id=hackathon_id,
                                                              azure_key_id=azure_key.id)
        # avoid duplicate hackathon azure key
        if hackathon_azure_key is None:
            db_adapter.add_object_kwargs(HackathonAzureKey,
                                         hackathon_id=hackathon_id,
                                         azure_key_id=azure_key.id)
            db_adapter.commit()
        else:
            log.debug('hackathon azure key exists')

        return cert_url

    def get_certificates(self, hackathon_id):
        hackathon_azure_keys = db_adapter.find_all_objects_by(HackathonAzureKey, hackathon_id=hackathon_id)
        if hackathon_azure_keys is None:
            log.error('hackathon [%s] has no certificates' % hackathon_id)
            return None
        certificates = []
        for hackathon_azure_key in hackathon_azure_keys:
            dic = db_adapter.get_object(AzureKey, hackathon_azure_key.azure_key_id).dic()
            certificates.append(dic)
        return certificates

    def delete_certificate(self, certificate_id, hackathon_id):
        certificate_id = int(certificate_id)
        hackathon_id = int(hackathon_id)
        hackathon_azure_keys = db_adapter.find_all_objects_by(HackathonAzureKey, hackathon_id=hackathon_id)
        if hackathon_azure_keys is None:
            log.error('hackathon [%d] has no certificates' % hackathon_id)
            return False
        azure_key_ids = map(lambda x: x.azure_key_id, hackathon_azure_keys)
        if certificate_id not in azure_key_ids:
            log.error('hackathon [%d] has no certificate [%d]' % (hackathon_id, certificate_id))
            return False
        certificate = db_adapter.get_object(AzureKey, certificate_id)
        db_adapter.delete_object(certificate)
        db_adapter.commit()
        return True


azure_management = AzureManagement()


# if __name__ == '__main__':
#     azure_management = AzureManagement()
#     cert_url = azure_management.create_certificate('guhr34nfj', 'fhdufew3', 1)
#     print cert_url