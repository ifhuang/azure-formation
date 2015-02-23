__author__ = 'Yifu Huang'

from src.azureformation.database import (
    db_adapter
)
from src.azureformation.database.models import (
    AzureLog
)
from src.azureformation.log import (
    log
)
from src.azureformation.enum import (
    ALStatus
)
import time
import os
import json

# -------------------------------------------------- constants --------------------------------------------------#
# project name
AZURE_FORMATION = 'Azure Formation'
# resource status in program
READY_ROLE = 'ReadyRole'
STOPPED_VM = 'StoppedVM'
STOPPED_DEALLOCATED = 'StoppedDeallocated'
# os family name
WINDOWS = 'Windows'
LINUX = 'Linux'
# async wait name
WAIT_FOR_ASYNC = 'wait for async'
# async wait constants
ASYNC_TICK = 30
ASYNC_LOOP = 60
DEPLOYMENT_TICK = 30
DEPLOYMENT_LOOP = 60
VIRTUAL_MACHINE_TICK = 30
VIRTUAL_MACHINE_LOOP = 60
# async wait status
IN_PROGRESS = 'InProgress'
SUCCEEDED = 'Succeeded'
# template name
T_EXPR_NAME = 'expr_name'
T_STORAGE_ACCOUNT = 'storage_account'
T_CONTAINER = 'container'
T_CLOUD_SERVICE = 'cloud_service'
T_DEPLOYMENT = 'deployment'
T_VIRTUAL_MACHINES = 'virtual_machines'
R_VIRTUAL_ENVIRONMENTS = 'virtual_environments'
# message when resource not found in azure
NOT_FOUND = 'Not found (Not Found)'
# -------------------------------------------------- constants --------------------------------------------------#


def commit_azure_log(experiment, operation, status, note=None):
    """
    Commit azure log to database
    :param experiment:
    :param operation:
    :param status:
    :param note:
    :return:
    """
    db_adapter.add_object_kwargs(AzureLog,
                                 experiment=experiment,
                                 operation=operation,
                                 status=status,
                                 note=note)
    db_adapter.commit()


# todo improve async (no sleep)
def wait_for_async(service, request_id, second_per_loop, loop):
    """
    Wait for async operation, up to second_per_loop * loop
    :param request_id:
    :return:
    """
    count = 0
    result = service.get_operation_status(request_id)
    while result.status == IN_PROGRESS:
        log.debug('%s [%s] loop count [%d]' % (WAIT_FOR_ASYNC, request_id, count))
        count += 1
        if count > loop:
            log.error('Timed out waiting for async operation to complete.')
            return False
        time.sleep(second_per_loop)
        result = service.get_operation_status(request_id)
    if result.status != SUCCEEDED:
        log.error(vars(result))
        if result.error:
            log.error(result.error.code)
            log.error(vars(result.error))
        log.error('Asynchronous operation did not succeed.')
        return False
    return True


def load_template(experiment, operation):
    """
    Load json based template into dictionary
    :param experiment:
    :return:
    """
    # make sure template url exists
    if os.path.isfile(experiment.template.url):
        try:
            raw_template = json.load(file(experiment.template.url))
        except Exception as e:
            m = 'ugly json format: %s' % e.message
            commit_azure_log(experiment, operation, ALStatus.FAIL, m)
            log.error(e)
            return None
    else:
        m = '%s not exist' % experiment.template.url
        commit_azure_log(experiment, operation, ALStatus.FAIL, m)
        log.error(m)
        return None
    template_config = {
        T_EXPR_NAME: raw_template[T_EXPR_NAME],
        T_STORAGE_ACCOUNT: raw_template[T_STORAGE_ACCOUNT],
        T_CONTAINER: raw_template[T_CONTAINER],
        T_CLOUD_SERVICE: raw_template[T_CLOUD_SERVICE],
        T_DEPLOYMENT: raw_template[T_DEPLOYMENT],
        T_VIRTUAL_MACHINES: raw_template[R_VIRTUAL_ENVIRONMENTS]
    }
    return template_config
