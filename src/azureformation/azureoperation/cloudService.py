__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.subscription import (
    Subscription
)
from src.azureformation.azureoperation.utility import (
    commit_azure_log
)
from src.azureformation.log import (
    log
)
from src.azureformation.database import (
    db_adapter
)
from src.azureformation.database.models import (
    AzureCloudService
)
from src.azureformation.enum import (
    ALOperation,
    ALStatus,
    ACSStatus,
    CLOUD_SERVICE
)


class CloudService:
    """
    Cloud service is used as DNS for azure virtual machines
    """

    def __init__(self, service):
        self.service = service
        self.subscription = Subscription(service)

    def create_cloud_service(self, name, label, location, experiment):
        """
        If cloud service not exist in azure subscription, then create it
        Else reuse cloud service in azure subscription
        :return:
        """
        commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.START)
        # avoid duplicate cloud service
        if not self.service.cloud_service_exists(name):
            # avoid name already taken by others
            if not self.service.check_hosted_service_name_availability(name).result:
                m = '%s [%s] name not available' % (CLOUD_SERVICE, name)
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, m)
                log.error(m)
                return False
            # avoid no available subscription remained
            if self.subscription.get_available_cloud_service_count() < 1:
                m = '%s [%s] subscription not enough' % (CLOUD_SERVICE, name)
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, m)
                log.error(m)
                return False
            # delete old cloud service info in database, cascade delete old deployment, old virtual machine,
            # old vm endpoint and old vm config
            db_adapter.delete_all_objects(AzureCloudService, name=name)
            db_adapter.commit()
            try:
                self.service.create_hosted_service(name=name,
                                                   label=label,
                                                   location=location)
            except Exception as e:
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, e.message)
                log.error(e)
                return False
            # make sure cloud service is created
            if not self.service.cloud_service_exists(name):
                m = '%s %s created but not exist' % (CLOUD_SERVICE, ['service_name'])
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, m)
                log.error(m)
                return False
            else:
                db_adapter.add_object_kwargs(AzureCloudService,
                                             name=name,
                                             label=label,
                                             location=location,
                                             status=ACSStatus.CREATED,
                                             experiment=experiment)
                db_adapter.commit()
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.END)
        else:
            # check whether cloud service created by this function before
            if db_adapter.count(AzureCloudService, name=name) == 0:
                m = '%s %s exist but not created by this function before' % (CLOUD_SERVICE, name)
                db_adapter.add_object_kwargs(AzureCloudService,
                                             name=name,
                                             label=label,
                                             location=location,
                                             status=ACSStatus.CREATED,
                                             experiment=experiment)
                db_adapter.commit()
            else:
                m = '%s %s exist and created by this function before' % (CLOUD_SERVICE, name)
            commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.END, m)
            log.debug(m)
        return True

    # todo update cloud service
    def update_cloud_service(self):
        raise NotImplementedError

    # todo delete cloud service
    def delete_cloud_service(self):
        raise NotImplementedError