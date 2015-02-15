__author__ = 'Yifu Huang'


from src.app.azureformation.service import Service
from src.app.azureformation.subscription import Subscription
from src.app.credentials import *

service = Service(SUBSCRIPTION_ID, PEM_CERTIFICATE, MANAGEMENT_HOST)
subscription = Subscription(service)
print subscription.get_available_storage_account_count()
print subscription.get_available_cloud_service_count()
print subscription.get_available_core_count()