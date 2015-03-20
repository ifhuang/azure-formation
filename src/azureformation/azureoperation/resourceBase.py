__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.service import (
    Service,
)
from src.azureformation.azureoperation.subscription import(
    Subscription,
)


class ResourceBase(object):

    def __init__(self, azure_key_id):
        self.azure_key_id = azure_key_id
        self.service = Service(self.azure_key_id)
        self.subscription = Subscription(self.service)