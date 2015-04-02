__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.utility import (
    load_template_from_experiment,
)
from src.azureformation.azureoperation.templateUnit import (
    TemplateUnit
)


class TemplateFramework():
    VIRTUAL_ENVIRONMENTS = 'virtual_environments'

    def __init__(self, experiment_id):
        self.template = load_template_from_experiment(experiment_id)

    def get_template_units(self):
        return map(TemplateUnit, self.template[self.VIRTUAL_ENVIRONMENTS])