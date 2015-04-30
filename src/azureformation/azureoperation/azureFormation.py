__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.templateFramework import (
    TemplateFramework,
)
from src.azureformation.azureoperation.utility import (
    MDL_CLS_FUNC,
    run_job,
)


class AzureFormation:
    """
    Azure cloud service management
    For logic: besides resources created by this program itself, it can reuse other storage,
    container, cloud service and deployment exist in azure (by sync them into database)
    For template: a template consists of a list of virtual environments, and a virtual environment
    is a virtual machine with its storage account, container, cloud service and deployment
    Notice: It requires exclusive access when Azure performs an async operation on a deployment
    """

    def __init__(self, azure_key_id):
        self.azure_key_id = azure_key_id

    def create(self, experiment_id):
        template_framework = TemplateFramework(experiment_id)
        for template_unit in template_framework.get_template_units():
            # create storage account
            run_job(MDL_CLS_FUNC[0],
                    (self.azure_key_id, ),
                    (experiment_id, template_unit))

    def stop(self, experiment_id, need_status):
        template_framework = TemplateFramework(experiment_id)
        for template_unit in template_framework.get_template_units():
            # stop virtual machine
            run_job(MDL_CLS_FUNC[17],
                    (self.azure_key_id, ),
                    (experiment_id, template_unit, need_status))
