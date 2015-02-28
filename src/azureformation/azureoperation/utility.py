__author__ = 'Yifu Huang'

from src.azureformation.database import (
    db_adapter,
)
from src.azureformation.database.models import (
    AzureLog,
    AzureStorageAccount,
    AzureCloudService,
    AzureDeployment,
    AzureVirtualMachine,
    AzureEndpoint,
    VirtualEnvironment,
)
from azure.servicemanagement import (
    ConfigurationSet,
    ConfigurationSetInputEndpoint,
)

# -------------------------------------------------- constants --------------------------------------------------#
# project name
AZURE_FORMATION = 'Azure Formation'
# async wait constants
ASYNC_TICK = 30
ASYNC_LOOP = 60
DEPLOYMENT_TICK = 30
DEPLOYMENT_LOOP = 60
VIRTUAL_MACHINE_TICK = 30
VIRTUAL_MACHINE_LOOP = 60
PORT_BOUND = 65536
# endpoint constants
ENDPOINT_PREFIX = 'AUTO-'
ENDPOINT_PROTOCOL = 'TCP'
# virtual machine constants
READY_ROLE = 'ReadyRole'


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
def commit_azure_deployment(name, slot, status, cloud_service_name, experiment):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    db_adapter.add_object_kwargs(AzureDeployment,
                                 name=name,
                                 slot=slot,
                                 status=status,
                                 cloud_service=cs,
                                 experiment=experiment)
    db_adapter.commit()


def contain_azure_deployment(cloud_service_name, deployment_slot):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    return db_adapter.count(AzureDeployment,
                            slot=deployment_slot,
                            cloud_service_id=cs.id) != 0


def delete_azure_deployment(cloud_service_name, deployment_slot):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    db_adapter.delete_all_objects(AzureDeployment,
                                  slot=deployment_slot,
                                  cloud_service_id=cs.id)
    db_adapter.commit()


# --------------------------------------------- azure virtual machine ---------------------------------------------#
def commit_azure_virtual_machine(name, label, status, dns, public_ip, private_ip,
                                 cloud_service_name, deployment_name, experiment, virtual_environment):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    dm = db_adapter.find_first_object(AzureDeployment, name=deployment_name, cloud_service=cs)
    vm = db_adapter.add_object_kwargs(AzureVirtualMachine,
                                      name=name,
                                      label=label,
                                      status=status,
                                      dns=dns,
                                      public_ip=public_ip,
                                      private_ip=private_ip,
                                      deployment=dm,
                                      experiment=experiment,
                                      virtual_environment=virtual_environment)
    db_adapter.commit()
    return vm


def contain_azure_virtual_machine(cloud_service_name, deployment_name, virtual_machine_name):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    dm = db_adapter.find_first_object(AzureDeployment, name=deployment_name, cloud_service=cs)
    return db_adapter.count(AzureVirtualMachine,
                            name=virtual_machine_name,
                            deployment_id=dm.id) != 0


def delete_azure_virtual_machine(cloud_service_name, deployment_name, virtual_machine_name):
    cs = db_adapter.find_first_object(AzureCloudService, name=cloud_service_name)
    dm = db_adapter.find_first_object(AzureDeployment, name=deployment_name, cloud_service=cs)
    db_adapter.delete_all_objects(AzureVirtualMachine,
                                  name=virtual_machine_name,
                                  deployment_id=dm.id)
    db_adapter.commit()


# --------------------------------------------- azure endpoint ---------------------------------------------#
def commit_azure_endpoint(name, protocol, public_port, private_port, virtual_machine):
    db_adapter.add_object_kwargs(AzureEndpoint,
                                 name=name,
                                 protocol=protocol,
                                 public_port=public_port,
                                 private_port=private_port,
                                 virtual_machine=virtual_machine)
    db_adapter.commit()


def find_unassigned_endpoint(endpoint, assigned_endpoints):
    """
    Be careful data type of input parameters
    :param endpoint: int
    :param assigned_endpoints: list of str
    :return:
    """
    while str(endpoint) in assigned_endpoints:
        endpoint = (endpoint + 1) % PORT_BOUND
    return endpoint


# --------------------------------------------- virtual environment ---------------------------------------------#
def commit_virtual_environment(provider, name, image, status, remote_provider, remote_paras, experiment):
    ve = db_adapter.add_object_kwargs(VirtualEnvironment,
                                      provider=provider,
                                      name=name,
                                      image=image,
                                      status=status,
                                      remote_provider=remote_provider,
                                      remote_paras=remote_paras,
                                      experiment=experiment)
    db_adapter.commit()
    return ve


# --------------------------------------------- network config ---------------------------------------------#
def add_endpoint_to_network_config(network_config, public_endpoint, private_endpoint):
    """
    Return a new network config
    :param network_config:
    :param public_endpoint:
    :param private_endpoint:
    :return:
    """
    new_network_config = ConfigurationSet()
    new_network_config.configuration_set_type = network_config.configuration_set_type
    if network_config.input_endpoints is not None:
        for input_endpoint in network_config.input_endpoints.input_endpoints:
            new_network_config.input_endpoints.input_endpoints.append(
                ConfigurationSetInputEndpoint(input_endpoint.name,
                                              input_endpoint.protocol,
                                              input_endpoint.port,
                                              input_endpoint.local_port)
            )
    new_network_config.input_endpoints.input_endpoints.append(
        ConfigurationSetInputEndpoint(ENDPOINT_PREFIX + str(public_endpoint),
                                      ENDPOINT_PROTOCOL,
                                      str(public_endpoint),
                                      str(private_endpoint))
    )
    return new_network_config


def delete_endpoint_from_network_config(network_config, private_endpoint):
    """
    Return a new network config
    :param network_config:
    :param private_endpoint:
    :return:
    """
    new_network_config = ConfigurationSet()
    new_network_config.configuration_set_type = network_config.configuration_set_type
    if network_config.input_endpoints is not None:
        for input_endpoint in network_config.input_endpoints.input_endpoints:
            if input_endpoint.local_port != str(private_endpoint):
                new_network_config.input_endpoints.input_endpoints.append(
                    ConfigurationSetInputEndpoint(input_endpoint.name,
                                                  input_endpoint.protocol,
                                                  input_endpoint.port,
                                                  input_endpoint.local_port)
                )
    return new_network_config