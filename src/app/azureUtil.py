__author__ = 'Yifu Huang'

from src.app.database import *
from src.app.log import *
import time

# operation name
CREATE_STORAGE_ACCOUNT = 'create_storage_account'
CREATE_CLOUD_SERVICE = 'create_cloud_service'
CREATE_VIRTUAL_MACHINES = 'create_virtual_machines'
CREATE_VIRTUAL_MACHINES_DEPLOYMENT = 'create_virtual_machines_deployment'
CREATE_VIRTUAL_MACHINES_ROLE = 'create_virtual_machines_role'
# operation status
START = 'start'
FAIL = 'fail'
END = 'end'
# resource name
STORAGE_ACCOUNT = 'storage account'
CLOUD_SERVICE = 'cloud service'
# resource status
RUNNING = 'Running'
# os family name
WINDOWS = 'Windows'
LINUX = 'Linux'


def user_operation_commit(user_template, operation, status, note=None):
    """
    Commit user operation to database
    :param operation:
    :param status:
    :param note:
    :return:
    """
    user_operation = UserOperation(user_template, operation, status, note)
    db.session.add(user_operation)
    db.session.commit()


def user_resource_commit(user_template, type, name, status, cs_id=None):
    """
    Commit user resource to database
    :param type:
    :param name:
    :param status:
    :return:
    """
    user_resource = UserResource(user_template, type, name, status, cs_id)
    db.session.add(user_resource)
    db.session.commit()


def vm_endpoint_commit(name, protocol, port, local_port, cs):
    """
    Commit vm endpoint to database before create vm
    :param name:
    :param protocol:
    :param port:
    :param local_port:
    :param cs:
    :return:
    """
    vm_endpoint = VMEndpoint(name, protocol, port, local_port, cs)
    db.session.add(vm_endpoint)
    db.session.commit()


def wait_for_async(sms, request_id, second_per_loop, loop):
    """
    Wait for async operation, up to second_per_loop * loop
    :param request_id:
    :return:
    """
    count = 0
    result = sms.get_operation_status(request_id)
    while result.status == 'InProgress':
        log.debug('_wait_for_async [%s] loop count [%d]' % (request_id, count))
        count += 1
        if count > loop:
            log.debug('Timed out waiting for async operation to complete.')
            return False
        time.sleep(second_per_loop)
        result = sms.get_operation_status(request_id)
    if result.status != 'Succeeded':
        log.debug(vars(result))
        if result.error:
            log.debug(result.error.code)
            log.debug(vars(result.error))
        log.debug('Asynchronous operation did not succeed.')
        return False
    return True
