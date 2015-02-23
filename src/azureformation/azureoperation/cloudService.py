__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.subscription import (
    Subscription
)
from src.azureformation.azureoperation.utility import (
    AZURE_FORMATION,
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

create_cloud_service_error = [
    '%s [%s] %s',
    '%s [%s] name not available',
    '%s [%s] subscription not enough',
    '%s [%s] created but not exist'
]
create_cloud_service_info = [
    '%s [%s] created',
    '%s [%s] exist but not created by %s before',
    '%s [%s] exist and created by %s before'
]


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
        # avoid duplicate cloud service in azure subscription
        if not self.service.cloud_service_exists(name):
            # avoid name already taken by other azure subscription
            if not self.service.check_hosted_service_name_availability(name).result:
                m = create_cloud_service_error[1] % (CLOUD_SERVICE, name)
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, m, 1)
                log.error(m)
                return False
            # avoid no available subscription remained
            if self.subscription.get_available_cloud_service_count() < 1:
                m = create_cloud_service_error[2] % (CLOUD_SERVICE, name)
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, m, 2)
                log.error(m)
                return False
            # delete old azure cloud service in database, cascade delete old azure deployment,
            # old azure virtual machine, old azure end point
            db_adapter.delete_all_objects(AzureCloudService, name=name)
            db_adapter.commit()
            try:
                self.service.create_hosted_service(name=name,
                                                   label=label,
                                                   location=location)
            except Exception as e:
                m = create_cloud_service_error[0] % (CLOUD_SERVICE, name, e.message)
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, m, 0)
                log.error(e)
                return False
            # make sure cloud service is created
            if not self.service.cloud_service_exists(name):
                m = create_cloud_service_error[3] % (CLOUD_SERVICE, name)
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.FAIL, m, 3)
                log.error(m)
                return False
            else:
                m = create_cloud_service_info[0] % (CLOUD_SERVICE, name)
                db_adapter.add_object_kwargs(AzureCloudService,
                                             name=name,
                                             label=label,
                                             location=location,
                                             status=ACSStatus.CREATED,
                                             experiment=experiment)
                db_adapter.commit()
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.END, m, 0)
                log.debug(m)
        else:
            # check whether cloud service created by this function before
            if db_adapter.count(AzureCloudService, name=name) == 0:
                m = create_cloud_service_info[1] % (CLOUD_SERVICE, name, AZURE_FORMATION)
                db_adapter.add_object_kwargs(AzureCloudService,
                                             name=name,
                                             label=label,
                                             location=location,
                                             status=ACSStatus.CREATED,
                                             experiment=experiment)
                db_adapter.commit()
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.END, m, 1)
            else:
                m = create_cloud_service_info[2] % (CLOUD_SERVICE, name, AZURE_FORMATION)
                commit_azure_log(experiment, ALOperation.CREATE_CLOUD_SERVICE, ALStatus.END, m, 2)
            log.debug(m)
        return True

    # todo update cloud service
    def update_cloud_service(self):
        raise NotImplementedError

    # todo delete cloud service
    def delete_cloud_service(self):
        raise NotImplementedError