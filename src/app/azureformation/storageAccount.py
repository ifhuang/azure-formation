__author__ = 'Yifu Huang'

from src.app.azureformation.subscription import Subscription
from src.app.azureformation.utility import NOT_FOUND, commit_azure_log, ALStatus, STORAGE_ACCOUNT
from src.app.log import log
from src.app.database import db_adapter
from src.app.database.models import AzureStorageAccount
from src.app.enum import ALOperation


class StorageAccount:
    """
    Storage account is used by azure virtual machines to store their disks
    The status of storage account is defined in ASAStatus of enum.py
    """

    def __init__(self, service):
        self.service = service
        self.subscription = Subscription(service)

    def create_storage_account(self, experiment, name, description, label, location):
        """
        If storage account not exist in azure, then create it
        Else reuse storage account in azure
        :return:
        """
        commit_azure_log(experiment, ALOperation.CREATE_STORAGE_ACCOUNT, ALStatus.START)
        # avoid duplicate storage account
        if not self.__storage_account_exists(name):
            # delete old info in database
            db_adapter.delete_all_objects(UserResource, type=STORAGE_ACCOUNT, name=storage_account['service_name'])
            db_adapter.commit()
            try:
                result = self.service.create_storage_account(name,
                                                             description,
                                                             label,
                                                             location)
            except Exception as e:
                user_operation_commit(self.user_template, CREATE_STORAGE_ACCOUNT, FAIL, e.message)
                log.error(e)
                return False
            # make sure async operation succeeds
            if not wait_for_async(self.service, result.request_id, ASYNC_TICK, ASYNC_LOOP):
                m = WAIT_FOR_ASYNC + ' ' + FAIL
                user_operation_commit(self.user_template, CREATE_STORAGE_ACCOUNT, FAIL, m)
                log.error(m)
                return False
            # make sure storage account exists
            if not self.__storage_account_exists(storage_account['service_name']):
                m = '%s %s created but not exist' % (STORAGE_ACCOUNT, storage_account['service_name'])
                user_operation_commit(self.user_template, CREATE_STORAGE_ACCOUNT, FAIL, m)
                log.error(m)
                return False
            else:
                user_resource_commit(self.user_template, STORAGE_ACCOUNT, storage_account['service_name'], RUNNING)
                user_operation_commit(self.user_template, CREATE_STORAGE_ACCOUNT, END)
        else:
            # check whether storage account created by this function before
            if db_adapter.count(AzureStorageAccount, name=name) == 0:
                m = '%s %s exist but not created by this function before' % \
                    (STORAGE_ACCOUNT, storage_account['service_name'])
                user_resource_commit(self.user_template, STORAGE_ACCOUNT, storage_account['service_name'], RUNNING)
            else:
                m = '%s %s exist and created by this function before' % (STORAGE_ACCOUNT, name)
            user_operation_commit(self.user_template, CREATE_STORAGE_ACCOUNT, END, m)
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
        Check whether specific storage account exist in azure
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