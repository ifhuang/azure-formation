__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.subscription import(
    Subscription,
)
from src.azureformation.azureoperation.utility import (
    AZURE_FORMATION,
    ASYNC_TICK,
    ASYNC_LOOP,
    commit_azure_log,
    commit_azure_storage_account,
    contain_azure_storage_account,
    delete_azure_storage_account,
)
from src.azureformation.log import (
    log,
)
from src.azureformation.enum import (
    STORAGE_ACCOUNT,
    ALOperation,
    ALStatus,
    ASAStatus,
)

create_storage_account_error = [
    '%s [%s] %s',
    '%s [%s] name not available',
    '%s [%s] subscription not enough',
    '%s [%s] wait for async fail',
    '%s [%s] created but not exist'
]
create_storage_account_info = [
    '%s [%s] created',
    '%s [%s] exist and created by %s before',
    '%s [%s] exist but not created by %s before',
]


class StorageAccount:
    """
    Storage account is used by azure virtual machines to store their disks
    """

    def __init__(self, service):
        self.service = service
        self.subscription = Subscription(service)

    def create_storage_account(self, name, description, label, location, experiment):
        """
        If storage account not exist in azure subscription, then create it
        Else reuse storage account in azure subscription
        :return:
        """
        commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.START)
        # avoid duplicate storage account in azure subscription
        if not self.service.storage_account_exists(name):
            # avoid name already taken by other azure subscription
            if not self.service.check_storage_account_name_availability(name).result:
                m = create_storage_account_error[1] % (STORAGE_ACCOUNT, name)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, m, 1)
                log.error(m)
                return False
            # avoid no available subscription remained
            if self.subscription.get_available_storage_account_count() < 1:
                m = create_storage_account_error[2] % (STORAGE_ACCOUNT, name)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, m, 2)
                log.error(m)
                return False
            # delete old azure storage account in database
            delete_azure_storage_account(name)
            try:
                result = self.service.create_storage_account(name,
                                                             description,
                                                             label,
                                                             location)
            except Exception as e:
                m = create_storage_account_error[0] % (STORAGE_ACCOUNT, name, e.message)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, m, 0)
                log.error(e)
                return False
            # make sure async operation succeed
            if not self.service.wait_for_async(result.request_id, ASYNC_TICK, ASYNC_LOOP):
                m = create_storage_account_error[3] % (STORAGE_ACCOUNT, name)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, m, 3)
                log.error(m)
                return False
            # make sure storage account exist
            if not self.service.storage_account_exists(name):
                m = create_storage_account_error[4] % (STORAGE_ACCOUNT, name)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, m, 4)
                log.error(m)
                return False
            else:
                m = create_storage_account_info[0] % (STORAGE_ACCOUNT, name)
                commit_azure_storage_account(name, description, label, location, ASAStatus.ONLINE, experiment)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.END, m, 0)
                log.debug(m)
        else:
            # check whether storage account created by azure formation before
            if contain_azure_storage_account(name):
                m = create_storage_account_info[1] % (STORAGE_ACCOUNT, name, AZURE_FORMATION)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.END, m, 1)
            else:
                m = create_storage_account_info[2] % (STORAGE_ACCOUNT, name, AZURE_FORMATION)
                commit_azure_storage_account(name, description, label, location, ASAStatus.ONLINE, experiment)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.END, m, 2)
            log.debug(m)
        return True

    # todo update storage account
    def update_storage_account(self):
        raise NotImplementedError

    # todo delete storage account
    def delete_storage_account(self):
        raise NotImplementedError
