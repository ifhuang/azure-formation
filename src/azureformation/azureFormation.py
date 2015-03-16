__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.templateFramework import (
    TemplateFramework,
)
from src.azureformation.azureoperation.storageAccount import (
    StorageAccount,
)
from src.azureformation.azureoperation.cloudService import (
    CloudService,
)
from src.azureformation.azureoperation.virtualMachine import (
    VirtualMachine,
)


class AzureFormation():
    """
    Azure cloud service management
    For logic: besides resources created by this program itself, it can reuse other storage,
    container, cloud service and deployment exist in azure (by sync them into database)
    For template: a template consists of a list of virtual environments, and a virtual environment
    is a virtual machine with its storage account, container, cloud service and deployment
    Notice: It requires exclusive access when Azure performs an async operation on a deployment
    """

    def __init__(self, service):
        self.service = service
        self.storage_account = StorageAccount(self.service)
        self.cloud_service = CloudService(self.service)
        self.virtual_machine = VirtualMachine(self.service)

    def create(self, experiment):
        template_framework = TemplateFramework(experiment)
        for template_unit in template_framework.get_template_units():
            self.storage_account.create_storage_account(experiment, template_unit)
            self.cloud_service.create_cloud_service(experiment, template_unit)
            self.virtual_machine.create_virtual_machine(experiment, template_unit)