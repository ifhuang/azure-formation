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
from src.azureformation.enum import (
    AVMStatus
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

    # new storage account testppp need manual delete
    def test_create_storage_account(self):
        storage = StorageAccount(self.service)
        result = storage.create_storage_account(None, 'testpp', 'description', 'label', 'China East')
        self.assertTrue(result)
        result = storage.create_storage_account(None, 'testpp', 'description', 'label', 'China East')
        self.assertTrue(result)
        result = storage.create_storage_account(None, 'ossvhds', 'description', 'label', 'China East')
        self.assertFalse(result)
        result = storage.create_storage_account(None, 'testppp', 'description', 'label', 'China East')
        self.assertTrue(result)

    # new cloud service open-xml-host-2 need manual delete
    def test_create_cloud_service(self):
        cloud = CloudService(self.service)
        result = cloud.create_cloud_service(None, 'open-xml-host', 'label', 'China East')
        self.assertTrue(result)
        result = cloud.create_cloud_service(None, 'open-xml-host', 'label', 'China East')
        self.assertTrue(result)
        result = cloud.create_cloud_service(None, 'open-hackathon', 'label', 'China East')
        self.assertFalse(result)
        result = cloud.create_cloud_service(None, 'open-xml-host-2', 'label', 'China East')
        self.assertTrue(result)

    # new cloud service ot-service-test need manual delete
    # new virtual machine ot-role-test-$(experiment.id) need manual delete
    def test_create_virtual_machine(self):
        experiment = db_adapter.add_object_kwargs(Experiment)
        db_adapter.commit()
        template_unit_json = \
            json.load(file('../src/azureformation/resources/test-template-1.js'))['virtual_environments'][0]
        storage = StorageAccount(self.service)
        sa = template_unit_json['storage_account']
        result = storage.create_storage_account(experiment,
                                                sa['service_name'],
                                                sa['description'],
                                                sa['label'],
                                                sa['location'])
        self.assertTrue(result)
        cloud = CloudService(self.service)
        cs = template_unit_json['cloud_service']
        result = cloud.create_cloud_service(experiment,
                                            cs['service_name'],
                                            cs['label'],
                                            cs['location'])
        self.assertTrue(result)
        vm = VirtualMachine(self.service)
        template_unit = TemplateUnit(template_unit_json)
        result = vm.create_virtual_machine(experiment, template_unit)
        self.assertTrue(result)
        result = vm.create_virtual_machine(experiment, template_unit)
        self.assertTrue(result)

    def test_assign_public_endpoints(self):
        endpoint = Endpoint(self.service)
        result = endpoint.assign_public_endpoints('ot-service-test', 'production', 'ot-role-test-7',
                                                  [81, 82, 83, 84, 85, 3390, 3391, 3392, 3393])
        self.assertIsNotNone(result)

    def test_release_public_endpoints(self):
        endpoint = Endpoint(self.service)
        result = endpoint.release_public_endpoints('ot-service-test', 'production', 'ot-role-test-7',
                                                   [81, 82, 83, 84, 85, 3390, 3391, 3392, 3393])
        self.assertTrue(result)

    def test_stop_virtual_machine(self):
        vm = VirtualMachine(self.service)
        result = vm.stop_virtual_machine(None, 'ot-service-test', 'ot-deployment-test', 'ot-role-test-7',
                                         AVMStatus.STOPPED)
        self.assertTrue(result)
        result = vm.stop_virtual_machine(None, 'ot-service-test', 'ot-deployment-test', 'ot-role-test-7',
                                         AVMStatus.STOPPED_DEALLOCATED)
        self.assertTrue(result)
        result = vm.stop_virtual_machine(None, 'ot-service-test', 'ot-deployment-test', 'ot-role-test-7',
                                         AVMStatus.STOPPED_DEALLOCATED)
        self.assertTrue(result)
        result = vm.stop_virtual_machine(None, 'ot-service-test', 'ot-deployment-test', 'ot-role-test-7',
                                         AVMStatus.STOPPED)
        self.assertFalse(result)

    def test_start_virtual_machine(self):
        vm = VirtualMachine(self.service)
        result = vm.start_virtual_machine(None, 'ot-service-test', 'ot-deployment-test', 'ot-role-test-7')
        self.assertTrue(result)
        result = vm.start_virtual_machine(None, 'ot-service-test', 'ot-deployment-test', 'ot-role-test-7')
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
