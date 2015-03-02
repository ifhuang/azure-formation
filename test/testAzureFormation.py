__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.service import (
    Service,
)
from src.azureformation.azureoperation.subscription import (
    Subscription,
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
from src.azureformation.azureoperation.templateUnit import (
    TemplateUnit,
)
from src.azureformation.azureoperation.endpoint import (
    Endpoint,
)
from src.azureformation.database import (
    db_adapter,
)
from src.azureformation.database.models import (
    Experiment,
)
from src.azureformation.credentials import (
    SUBSCRIPTION_ID,
    PEM_CERTIFICATE,
    MANAGEMENT_HOST,
)
import unittest
import json


class TestAzureFormation(unittest.TestCase):

    def setUp(self):
        self.service = Service(SUBSCRIPTION_ID, PEM_CERTIFICATE, MANAGEMENT_HOST)

    def test_subscription(self):
        subscription = Subscription(self.service)
        sa_count = subscription.get_available_storage_account_count()
        self.assertGreaterEqual(sa_count, 0)
        cs_count = subscription.get_available_cloud_service_count()
        self.assertGreaterEqual(cs_count, 0)
        c_count = subscription.get_available_core_count()
        self.assertGreaterEqual(c_count, 0)

    def test_create_storage_account(self):
        storage = StorageAccount(self.service)
        result = storage.create_storage_account('testpp', 'description', 'label', 'China East', None)
        self.assertTrue(result)
        result = storage.create_storage_account('testpp', 'description', 'label', 'China East', None)
        self.assertTrue(result)
        result = storage.create_storage_account('ossvhds', 'description', 'label', 'China East', None)
        self.assertFalse(result)
        result = storage.create_storage_account('testppp', 'description', 'label', 'China East', None)
        self.assertTrue(result)

    def test_create_cloud_service(self):
        cloud = CloudService(self.service)
        result = cloud.create_cloud_service('open-xml-host', 'label', 'China East', None)
        self.assertTrue(result)
        result = cloud.create_cloud_service('open-xml-host', 'label', 'China East', None)
        self.assertTrue(result)
        result = cloud.create_cloud_service('open-hackathon', 'label', 'China East', None)
        self.assertFalse(result)
        result = cloud.create_cloud_service('open-xml-host-2', 'label', 'China East', None)
        self.assertTrue(result)

    def test_create_virtual_machine(self):
        experiment = db_adapter.add_object_kwargs(Experiment)
        db_adapter.commit()
        template_unit_json = \
            json.load(file('../src/azureformation/resources/new-template-1.js'))['virtual_environments'][0]
        storage = StorageAccount(self.service)
        sa = template_unit_json['storage_account']
        result = storage.create_storage_account(sa['service_name'],
                                                sa['description'],
                                                sa['label'],
                                                sa['location'],
                                                experiment)
        self.assertTrue(result)
        cloud = CloudService(self.service)
        cs = template_unit_json['cloud_service']
        result = cloud.create_cloud_service(cs['service_name'],
                                            cs['label'],
                                            cs['location'],
                                            experiment)
        self.assertTrue(result)
        vm = VirtualMachine(self.service)
        template_unit = TemplateUnit(template_unit_json)
        result = vm.create_virtual_machine(template_unit, experiment)
        self.assertTrue(result)
        result = vm.create_virtual_machine(template_unit, experiment)
        self.assertTrue(result)

    def test_assign_public_endpoints(self):
        endpoint = Endpoint(self.service)
        result = endpoint.assign_public_endpoints('open-tech-service', 'production', 'open-tech-role-69',
                                                  [81, 82, 83, 84, 85, 3390, 3391, 3392, 3393])
        self.assertIsNotNone(result)

    def test_release_public_endpoints(self):
        endpoint = Endpoint(self.service)
        result = endpoint.release_public_endpoints('open-tech-service', 'production', 'open-tech-role-69',
                                                   [81, 82, 83, 84, 85, 3390, 3391, 3392, 3393])
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
