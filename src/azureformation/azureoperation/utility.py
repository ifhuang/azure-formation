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
# message when resource not found in azure
NOT_FOUND = 'Not found (Not Found)'
# network configuration set type
NETWORK_CONFIGURATION = 'NetworkConfiguration'
# -------------------------------------------------- constants --------------------------------------------------#


def commit_azure_log(experiment, operation, status, note=None, code=None):
    """
    Commit azure log to database
    :param experiment:
    :param operation:
    :param status:
    :param code:
    :param note:
    :return:
    """
    db_adapter.add_object_kwargs(AzureLog,
                                 experiment=experiment,
                                 operation=operation,
                                 status=status,
                                 note=note,
                                 code=code)
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
