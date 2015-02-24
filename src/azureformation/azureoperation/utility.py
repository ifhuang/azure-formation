__author__ = 'Yifu Huang'

from src.azureformation.database import (
    db_adapter
)
from src.azureformation.database.models import (
    AzureLog,
    AzureStorageAccount,
    AzureCloudService,
    AzureDeployment,
    AzureVirtualMachine
)

# -------------------------------------------------- constants --------------------------------------------------#
# project name
AZURE_FORMATION = 'Azure Formation'
# resource status in program
READY_ROLE = 'ReadyRole'
STOPPED_VM = 'StoppedVM'
STOPPED_DEALLOCATED = 'StoppedDeallocated'
# async wait name
WAIT_FOR_ASYNC = 'wait for async'
WAIT_FOR_DEPLOYMENT = 'wait for deployment'
WAIT_FOR_VIRTUAL_MACHINE = 'wait for virtual machine'
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

# -------------------------------------------------- azure log --------------------------------------------------#


def commit_azure_log(experiment, operation, status, note=None, code=None):
    db_adapter.add_object_kwargs(AzureLog,
                                 experiment=experiment,
                                 operation=operation,
                                 status=status,
                                 note=note,
                                 code=code)
    db_adapter.commit()


# --------------------------------------------- azure storage account ---------------------------------------------#


def commit_azure_storage_account(name, description, label, location, status, experiment):
    db_adapter.add_object_kwargs(AzureStorageAccount,
                                 name=name,
                                 description=description,
                                 label=label,
                                 location=location,
                                 status=status,
                                 experiment=experiment)
    db_adapter.commit()


def contain_azure_storage_account(name):
    return db_adapter.count(AzureStorageAccount, name=name) != 0


def delete_azure_storage_account(name):
    db_adapter.delete_all_objects(AzureStorageAccount, name=name)
    db_adapter.commit()


# --------------------------------------------- azure cloud service ---------------------------------------------#


def commit_azure_cloud_service(name, label, location, status, experiment):
    db_adapter.add_object_kwargs(AzureCloudService,
                                 name=name,
                                 label=label,
                                 location=location,
                                 status=status,
                                 experiment=experiment)
    db_adapter.commit()


def contain_azure_cloud_service(name):
    return db_adapter.count(AzureCloudService, name=name) != 0


def delete_azure_cloud_service(name):
    db_adapter.delete_all_objects(AzureCloudService, name=name)
    db_adapter.commit()


# --------------------------------------------- azure deployment ---------------------------------------------#


def delete_azure_deployment(cloud_service_name, deployment_slot):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    db_adapter.delete_all_objects(AzureDeployment,
                                  slot=deployment_slot,
                                  cloud_service_id=cs.id)
    db_adapter.commit()


def commit_azure_deployment(name, slot, status, cloud_service_name, experiment):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    db_adapter.add_object_kwargs(AzureDeployment,
                                 name=name,
                                 slot=slot,
                                 status=status,
                                 cloud_service=cs,
                                 experiment=experiment)
    db_adapter.commit()


# --------------------------------------------- azure virtual machine ---------------------------------------------#


def commit_azure_virtual_machine():
    pass