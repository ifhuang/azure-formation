__author__ = 'Yifu Huang'

# resource type used by ALOperation
STORAGE_ACCOUNT = 'storage account'
CLOUD_SERVICE = 'cloud service'
DEPLOYMENT = 'deployment'
VIRTUAL_MACHINE = 'virtual machine'


class AKOwner:
    """
    For owner in db model AzureKey
    """
    User = 0
    Hackathon = 1


class EStatus:
    """
    For status in db model Experiment
    """
    Init = 0
    Starting = 1
    Running = 2
    Stopped = 3
    Deleted = 4
    Failed = 5
    Rollbacking = 6
    Rollbacked = 7


class VEProvider:
    """
    For provider in db model VirtualEnvironment
    """
    AzureVM = 0
    Docker = 1


class VEStatus:
    """
    For status in db model VirtualEnvironment
    """
    Init = 0
    Running = 1
    Stopped = 2
    Deleted = 3


class VERemoteProvider:
    """
    For remote provider in db model VirtualEnvironment
    """
    Guacamole = 0


class ALOperation:
    """
    For operation in db model AzureLog
    """
    CREATE = 'create'
    CREATE_STORAGE_ACCOUNT = CREATE + ' ' + STORAGE_ACCOUNT
    CREATE_CLOUD_SERVICE = CREATE + ' ' + CLOUD_SERVICE
    CREATE_DEPLOYMENT = CREATE + ' ' + DEPLOYMENT
    CREATE_VIRTUAL_MACHINE = CREATE + ' ' + VIRTUAL_MACHINE
    UPDATE = 'update'
    UPDATE_VIRTUAL_MACHINE = UPDATE + ' ' + VIRTUAL_MACHINE
    DELETE = 'delete'
    DELETE_DEPLOYMENT = DELETE + ' ' + DEPLOYMENT
    DELETE_VIRTUAL_MACHINE = DELETE + ' ' + VIRTUAL_MACHINE
    SHUTDOWN = 'shutdown'
    SHUTDOWN_VIRTUAL_MACHINE = SHUTDOWN + ' ' + VIRTUAL_MACHINE


class ALStatus:
    """
    For status in db model AzureLog
    """
    START = 'start'
    FAIL = 'fail'
    END = 'end'


class ASAStatus:
    """
    For status in db model AzureStorageAccount
    """
    ONLINE = 'Online'


class ACSStatus:
    """
    For status in db model AzureCloudService
    """
    CREATED = 'Created'


class ADStatus:
    """
    For status in db model AzureDeployment
    """
    RUNNING = 'Running'


class AVMStatus:
    """
    For status in db model AzureVirtualMachine
    """
    RUNNING = 'Running'
    STOPPED = 'Stopped'
