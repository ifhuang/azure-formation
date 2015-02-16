__author__ = 'Yifu Huang'

from src.azureformation.azureoperation.service import Service
from src.azureformation.azureoperation.subscription import Subscription
from src.azureformation.azureoperation.storageAccount import StorageAccount
from src.azureformation.azureoperation.cloudService import CloudService
from src.azureformation.credentials import SUBSCRIPTION_ID, PEM_CERTIFICATE, MANAGEMENT_HOST
import unittest


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

    def test_storage_account(self):
        storage = StorageAccount(self.service)
        result = storage.create_storage_account('testpp', 'description', 'label', 'China East', None)
        self.assertTrue(result)
        result = storage.create_storage_account('testpp', 'description', 'label', 'China East', None)
        self.assertTrue(result)
        result = storage.create_storage_account('ossvhds', 'description', 'label', 'China East', None)
        self.assertFalse(result)
        result = storage.create_storage_account('testppp', 'description', 'label', 'China East', None)
        self.assertTrue(result)

    def test_cloud_service(self):
        cloud = CloudService(self.service)
        result = cloud.create_cloud_service('open-xml-host', 'label', 'China East', None)
        self.assertTrue(result)
        result = cloud.create_cloud_service('open-hackathon', 'label', 'China East', None)
        self.assertFalse(result)
        result = cloud.create_cloud_service('open-xml-host-2', 'label', 'China East', None)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
