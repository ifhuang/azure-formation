__author__ = 'Yifu Huang'

from src.app.azureformation.subscription import Subscription
from src.app.azureformation.utility import (
    NOT_FOUND,
    ALStatus,
    ASYNC_TICK,
    ASYNC_LOOP,
    WAIT_FOR_ASYNC,
    commit_azure_log,
    wait_for_async
)
from src.app.log import log
from src.app.database import db_adapter
from src.app.database.models import AzureStorageAccount
from src.app.enum import ALOperation, ASAStatus, STORAGE_ACCOUNT


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
        # avoid duplicate storage account
        if not self.__storage_account_exists(name):
            # avoid name already taken by others
            if not self.service.check_storage_account_name_availability(name).result:
                m = '%s [%s] not available' % (STORAGE_ACCOUNT, name)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL)
                log.error(m)
                return False
            # delete old info in database
            db_adapter.delete_all_objects(AzureStorageAccount, name=name)
            db_adapter.commit()
            try:
                result = self.service.create_storage_account(name,
                                                             description,
                                                             label,
                                                             location)
            except Exception as e:
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, e.message)
                log.error(e)
                return False
            # make sure async operation succeeds
            if not wait_for_async(self.service, result.request_id, ASYNC_TICK, ASYNC_LOOP):
                m = WAIT_FOR_ASYNC + ' ' + ALStatus.FAIL
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, m)
                log.error(m)
                return False
            # make sure storage account exists
            if not self.__storage_account_exists(name):
                m = '%s [%s] created but not exist' % (STORAGE_ACCOUNT, name)
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.FAIL, m)
                log.error(m)
                return False
            else:
                db_adapter.add_object_kwargs(AzureStorageAccount,
                                             name=name,
                                             description=description,
                                             location=location,
                                             label=label,
                                             status=ASAStatus.ONLINE,
                                             experiment=experiment)
                db_adapter.commit()
                commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.END)
        else:
            # check whether storage account created by this function before
            if db_adapter.count(AzureStorageAccount, name=name) == 0:
                m = '%s [%s] exist but not created by this function before' % (STORAGE_ACCOUNT, name)
                db_adapter.add_object_kwargs(AzureStorageAccount,
                                             name=name,
                                             description=description,
                                             location=location,
                                             label=label,
                                             status=ASAStatus.ONLINE,
                                             experiment=experiment)
                db_adapter.commit()
            else:
                m = '%s [%s] exist and created by this function before' % (STORAGE_ACCOUNT, name)
            commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.END, m)
            log.debug(m)
        return True

    # todo update storage account
    def update_storage_account(self):
        raise NotImplementedError

    # todo delete storage account
    def delete_storage_account(self):
        raise NotImplementedError

    # --------------------------------------------helper function-------------------------------------------- #

    def __storage_account_exists(self, name):
        """
        Check whether specific storage account exist in specific azure subscription
        :param name:
        :return:
        """
        try:
            props = self.service.get_storage_account_properties(name)
        except Exception as e:
            if e.message != NOT_FOUND:
                log.error(e)
            return False
        return props is not None