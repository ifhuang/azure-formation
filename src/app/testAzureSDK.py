__author__ = 'Yifu Huang'

import constants
from azure import *
from azure.servicemanagement import *

# Connect to service management
subscription_id = constants.SUBSCRIPTION_ID
certificate_path = constants.PEM_CERTIFICATE
host = constants.MANAGEMENT_HOST

sms = ServiceManagementService(subscription_id, certificate_path, host)

# List available locations
result = sms.list_locations()
for location in result:
    print(location.name)